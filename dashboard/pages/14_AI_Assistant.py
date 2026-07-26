import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Allow relative imports from the parent directory
dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import apply_custom_theme, load_market_metrics, load_sector_metrics, load_company_metrics, to_percent

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")
apply_custom_theme()

st.title("🤖 Quant AI Assistant")
st.caption("Ask questions about the NIFTY 500 dataset, regimes, and risk/return metrics.")

# ── Sidebar: API Key Configuration ────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Enter your Groq API key to enable the AI assistant. It is not saved.",
    )
    st.markdown("[Get a free Groq API key](https://console.groq.com/keys)")
    
    st.divider()
    st.markdown("""
    **Context Loaded:**
    - ✅ NIFTY 50 Benchmark Data
    - ✅ Sector/Industry Performance
    - ✅ Top/Bottom Stock Outliers
    """)

# ── Construct the Dynamic Context (RAG-Lite) ──────────────────────
@st.cache_data(ttl=3600)
def build_system_prompt():
    try:
        market_metrics = load_market_metrics()
        sector_metrics = load_sector_metrics()
        company_metrics = load_company_metrics()
        
        market_md = market_metrics.to_markdown(index=False)
        sec = sector_metrics[["Regime", "Industry", "CAGR", "Annualized Volatility", "Sharpe Ratio (Rf=6.5%)", "Maximum Drawdown"]]
        sec_md = sec.to_markdown(index=False)
        
        # Get full sample top 10 and bottom 10 stocks by CAGR to give the AI some stock-level context
        full = company_metrics[company_metrics["Regime"] == "Full Sample"]
        top_10 = full.nlargest(10, "CAGR")[["Symbol", "Company Name", "Industry", "CAGR", "Sharpe Ratio (Rf=6.5%)"]]
        bottom_10 = full.nsmallest(10, "CAGR")[["Symbol", "Company Name", "Industry", "CAGR", "Sharpe Ratio (Rf=6.5%)"]]
        
        top_md = top_10.to_markdown(index=False)
        bot_md = bottom_10.to_markdown(index=False)
        
        prompt = f"""You are a professional Quantitative Financial Analyst AI embedded inside a dashboard that analyzes the NIFTY 500 universe (Indian equities) over a 10-year period, covering the pre-COVID, COVID-shock, and post-COVID regimes.

You must answer the user's questions factually based ONLY on the proprietary dataset provided below. If a user asks about specific numbers, sectors, or market performance, cite the data provided below. Do not make up metrics.

--- MARKET LEVEL METRICS (NIFTY 50 Benchmark) ---
{market_md}

--- SECTOR LEVEL METRICS (Aggregated Industry Performance) ---
{sec_md}

--- TOP 10 BEST PERFORMING STOCKS (Full 10-Year Sample by CAGR) ---
{top_md}

--- BOTTOM 10 WORST PERFORMING STOCKS (Full 10-Year Sample by CAGR) ---
{bot_md}

--- INSTRUCTIONS ---
1. Be professional, concise, and highly analytical. Talk like an institutional hedge fund manager.
2. If asked "Which sector was most volatile pre-covid?", look at the Pre-COVID regime in Sector Metrics and find the highest Annualized Volatility.
3. If asked about the market drop in March 2020, look at the COVID Shock regime in the Market Level Metrics.
4. If a user asks a question that cannot be answered using the provided data, politely inform them that you only have access to the aggregated dataset above.
"""
        return prompt
    except Exception as e:
        return f"Error loading context: {e}"

# ── Chat Interface ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask about sector performance, volatility, or the COVID crash..."):
    if not api_key:
        st.error("⚠️ Please enter your Groq API Key in the sidebar to use the Assistant.")
        st.stop()
        
    try:
        from groq import Groq
    except ImportError:
        st.error("The `groq` python package is not installed. Please install it to continue.")
        st.stop()

    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Call Groq API
    try:
        client = Groq(api_key=api_key)
        
        # Build the message payload, injecting the system prompt
        api_messages = [
            {"role": "system", "content": build_system_prompt()}
        ]
        # Append the actual chat history
        for msg in st.session_state.messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Streaming response
            for chunk in client.chat.completions.create(
                model="llama3-70b-8192",
                messages=api_messages,
                stream=True,
                temperature=0.2, # Low temp for analytical factualness
            ):
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"API Error: {str(e)}")
