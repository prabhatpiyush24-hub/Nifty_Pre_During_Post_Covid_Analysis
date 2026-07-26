import streamlit as st
import pandas as pd
from utils import load_market_metrics, load_sector_metrics, load_company_metrics

def sidebar_api_key_config():
    """Renders the API key configuration in the sidebar."""
    st.sidebar.markdown("# QuantNifty")
    st.sidebar.header("🤖 AI Assistant")
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        st.sidebar.success("API Key loaded from Secure Secrets!")
        st.session_state["groq_api_key"] = api_key
    except (FileNotFoundError, KeyError):
        # We use a persistent key so the value isn't lost on navigation
        api_key = st.sidebar.text_input(
            "Groq API Key",
            type="password",
            help="Enter your Groq API key to enable the AI assistant.",
            key="groq_key_input"
        )
        st.sidebar.markdown("[Get a free Groq API key](https://console.groq.com/keys)")
        st.sidebar.warning("For public access, add `GROQ_API_KEY` to your Streamlit Cloud Secrets.")
        st.session_state["groq_api_key"] = api_key
        
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='text-align: center; color: #94A3B8; font-size: 0.85em; margin-top: 20px; font-weight: 500; letter-spacing: 0.05em;'>"
        "MADE BY PIYUSH PRABHAT"
        "</div>", 
        unsafe_allow_html=True
    )
    return st.session_state.get("groq_api_key", "")

@st.cache_data(ttl=3600)
def build_base_system_prompt() -> str:
    """Builds the global context for the AI."""
    try:
        market_metrics = load_market_metrics()
        sector_metrics = load_sector_metrics()
        company_metrics = load_company_metrics()
        
        market_md = market_metrics.to_markdown(index=False)
        sec = sector_metrics[["Regime", "Industry", "CAGR", "Annualized Volatility", "Sharpe Ratio (Rf=6.5%)", "Maximum Drawdown"]]
        sec_md = sec.to_markdown(index=False)
        
        full = company_metrics[company_metrics["Regime"] == "Full Sample"]
        top_10 = full.nlargest(10, "CAGR")[["Symbol", "Company Name", "Industry", "CAGR"]]
        bottom_10 = full.nsmallest(10, "CAGR")[["Symbol", "Company Name", "Industry", "CAGR"]]
        
        prompt = f"""You are a professional Quantitative Financial Analyst AI embedded inside a dashboard that analyzes the NIFTY 500 universe (Indian equities) over a 10-year period, covering the pre-COVID, COVID-shock, and post-COVID regimes.

--- CORE DIRECTIVE ---
You MUST answer the user's questions factually based ONLY on the proprietary dataset provided below and the specific page context provided.
If a user asks a question that is entirely beyond the scope of the provided data (e.g. "Who is the CEO of Reliance?", "What is the weather?"), you may answer using your general knowledge, but you MUST strictly begin your answer with exactly:
"**This is beyond the scope of the dashboard's data, but generally speaking...**"

--- MARKET LEVEL METRICS (NIFTY 50 Benchmark) ---
{market_md}

--- SECTOR LEVEL METRICS (Aggregated Industry Performance) ---
{sec_md}

--- TOP 10 BEST PERFORMING STOCKS (Full 10-Year Sample by CAGR) ---
{top_10.to_markdown(index=False)}

--- BOTTOM 10 WORST PERFORMING STOCKS (Full 10-Year Sample by CAGR) ---
{bottom_10.to_markdown(index=False)}
"""
        return prompt
    except Exception as e:
        return f"Error loading global context: {e}"

def render_ai_chat(context_data: str, unique_key: str):
    """Renders a contextual AI chat interface."""
    api_key = sidebar_api_key_config()
    
    with st.expander("🤖 Ask AI about this section", expanded=False):
        history_key = f"ai_history_{unique_key}"
        if history_key not in st.session_state:
            st.session_state[history_key] = []
            
        # Create a container for chat messages
        chat_container = st.container()
        
        # Render existing messages
        with chat_container:
            for message in st.session_state[history_key]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Input form
        with st.form(key=f"form_{unique_key}", clear_on_submit=True):
            cols = st.columns([6, 1])
            prompt = cols[0].text_input("Ask a question about this data...", label_visibility="collapsed")
            submitted = cols[1].form_submit_button("Send")
            
        if submitted and prompt:
            if not api_key:
                st.error("⚠️ Please configure your Groq API Key in the sidebar.")
                return
                
            try:
                from groq import Groq
            except ImportError:
                st.error("The `groq` python package is not installed.")
                return
                
            # Add user message to history and render
            st.session_state[history_key].append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
                    
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    try:
                        client = Groq(api_key=api_key)
                        
                        # Build system prompt with specific context appended
                        system_prompt = build_base_system_prompt()
                        system_prompt += f"\n\n--- SPECIFIC PAGE CONTEXT ---\nThe user is currently looking at this specific data/graph. Prioritize this context when answering:\n{context_data}"
                        
                        api_messages = [{"role": "system", "content": system_prompt}]
                        
                        for msg in st.session_state[history_key]:
                            api_messages.append({"role": msg["role"], "content": msg["content"]})
                            
                        # Stream response
                        for chunk in client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=api_messages,
                            stream=True,
                            temperature=0.2,
                        ):
                            content = chunk.choices[0].delta.content
                            if content:
                                full_response += content
                                message_placeholder.markdown(full_response + "▌")
                                
                        message_placeholder.markdown(full_response)
                        st.session_state[history_key].append({"role": "assistant", "content": full_response})
                        
                    except Exception as e:
                        st.error(f"API Error: {str(e)}")
                        # Remove the failed user message from state
                        st.session_state[history_key].pop()
