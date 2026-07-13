import streamlit as st
from guardrails import safe_chat, log_usage
import logging

st.set_page_config(page_title="Chatbot with Guardrails", layout="centered")

st.title("🤖 Chatbot Demo with Enhanced Guardrails")
st.write("This dashboard demonstrates a chatbot with input/output validation, retries, timeouts, rate limits, logging, and content filtering.")

# Conversation history
if "history" not in st.session_state:
    st.session_state["history"] = []

user_text = st.text_input("Ask me something:")

if st.button("Submit"):
    try:
        reply = safe_chat(user_text)

        # Save conversation
        st.session_state["history"].append(("You", user_text))
        st.session_state["history"].append(("Bot", reply))

        # Display conversation
        st.subheader("Conversation")
        for role, msg in st.session_state["history"]:
            if role == "You":
                st.markdown(f"**You:** {msg}")
            else:
                st.markdown(f"**Bot:** {msg}")

        log_usage("Chatbot response processed", cost=0.002)
        st.success("✅ Chatbot response generated safely.")

    except Exception as e:
        logging.error(f"Error in chatbot flow: {e}")
        st.error(f"❌ Guardrail triggered: {e}")
