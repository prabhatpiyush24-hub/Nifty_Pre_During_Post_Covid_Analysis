import streamlit as st
import sys
from pathlib import Path

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import apply_custom_theme
from ai_core import build_base_system_prompt

st.set_page_config(page_title="Global AI Assistant", page_icon="🤖", layout="wide")
apply_custom_theme()

st.title("🤖 Global AI Assistant")
st.caption("Ask questions about the NIFTY 500 dataset, regimes, and risk/return metrics across the entire dashboard.")

# Get API key from session state or secrets
api_key = st.session_state.get("groq_api_key", "")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except (FileNotFoundError, KeyError):
        pass

if not api_key:
    st.warning("⚠️ Please enter your Groq API Key in the sidebar configuration to use the Assistant.")
    st.stop()

# ── Chat Interface ────────────────────────────────────────────────
if "global_messages" not in st.session_state:
    st.session_state.global_messages = []

# Display chat messages from history on app rerun
for message in st.session_state.global_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask about sector performance, volatility, or the COVID crash..."):
    try:
        from groq import Groq
    except ImportError:
        st.error("The `groq` python package is not installed. Please install it to continue.")
        st.stop()

    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.global_messages.append({"role": "user", "content": prompt})

    # Call Groq API
    try:
        client = Groq(api_key=api_key)
        
        # Build the message payload, injecting the system prompt
        api_messages = [
            {"role": "system", "content": build_base_system_prompt()}
        ]
        # Append the actual chat history
        for msg in st.session_state.global_messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Streaming response
            for chunk in client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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
        st.session_state.global_messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"API Error: {str(e)}")
