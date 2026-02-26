import streamlit as st
import google.generativeai as genai
import time
import os
from io import BytesIO

# --- CONFIGURATION ---
st.set_page_config(
    page_title="EGCSE Physical Science Tutor",
    page_icon="🔬",
    layout="wide"
)

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = ""

# --- SIDEBAR: Settings & Knowledge Upload ---
with st.sidebar:
    st.title("⚙️ Teacher Dashboard")
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    
    st.markdown("---")
    st.subheader("📚 Knowledge Base")
    st.info("Upload EGCSE Syllabuses, Past Papers, or Examiner Reports (PDF/Text) to 'train' the bot.")
    
    uploaded_files = st.file_uploader("Upload ECESWA Documents", accept_multiple_files=True, type=['pdf', 'txt'])
    
    if st.button("Process Documents"):
        if not api_key:
            st.error("Please enter an API Key first.")
        else:
            with st.spinner("Analyzing documents..."):
                # In a real RAG app, we would use a vector DB. 
                # For this Streamlit version, we'll append text to the context window.
                # Note: Gemini 1.5/2.5 Flash has a massive 1M+ token window, making this viable.
                combined_text = ""
                for file in uploaded_files:
                    if file.type == "application/pdf":
                        # Basic PDF text extraction logic would go here
                        combined_text += f"\n[Document: {file.name}]\n(Content extracted from PDF)\n"
                    else:
                        combined_text += f"\n[Document: {file.name}]\n{file.read().decode()}\n"
                
                st.session_state.knowledge_base = combined_text
                st.success(f"Loaded {len(uploaded_files)} documents into the bot's memory!")

# --- MAIN UI ---
st.title("🔬 EGCSE Physical Science AI Tutor")
st.caption("Aligned with Eswatini Exams Council (ECESWA) Standards")

# System Prompt - The "Brain" of the bot
SYSTEM_PROMPT = f"""
You are an expert Physical Science Teacher specializing in the Eswatini General Certificate of Secondary Education (EGCSE) syllabus (Subject 6888).
Your goal is to help Form 5 students prepare for their exams.

RULES:
1. Always align answers with EGCSE standards. 
2. Use specific terminology from ECESWA examiner reports (e.g., explaining why 'rate of flow of charge' is the correct definition for current).
3. If a student asks about a past paper question, guide them through the steps rather than just giving the answer.
4. Reference the provided Knowledge Base if available.
5. Use SI units and proper scientific notation as required by the syllabus.

KNOWLEDGE BASE CONTEXT:
{st.session_state.knowledge_base}
"""

# Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask a question about Physics or Chemistry..."):
    if not api_key:
        st.error("Teacher must provide an API Key in the sidebar.")
    else:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Response
        with st.chat_message("assistant"):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash-preview-09-2025",
                    system_instruction=SYSTEM_PROMPT
                )
                
                # Exponential Backoff for API Calls
                response_text = ""
                for attempt in range(5):
                    try:
                        chat = model.start_chat(history=[
                            {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                            for m in st.session_state.chat_history[:-1]
                        ])
                        response = chat.send_message(prompt)
                        response_text = response.text
                        break
                    except Exception as e:
                        if attempt == 4: raise e
                        time.sleep(2**attempt)

                st.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Created for Eswatini Educators. Support: [ECESWA Website](https://www.examscouncil.org.sz)")


