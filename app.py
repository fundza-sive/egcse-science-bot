import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import time

# --- PDF READING CAPABILITY ---
def extract_text(files):
    text_content = ""
    for file in files:
        try:
            if file.type == "application/pdf":
                reader = PdfReader(file)
                text_content += f"\n--- Start of Document: {file.name} ---\n"
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
            else:
                text_content += f"\n--- Start of Document: {file.name} ---\n"
                text_content += file.read().decode("utf-8")
        except Exception as e:
            text_content += f"\n(Could not read {file.name}: {str(e)})\n"
    return text_content

# --- CONFIGURATION ---
st.set_page_config(page_title="EGCSE Physical Science Tutor", page_icon="🔬", layout="wide")

# Initialize State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = ""

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Teacher Dashboard")
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Enter Gemini API Key:", type="password")
    
    st.markdown("---")
    st.subheader("📚 Knowledge Base")
    st.write("Current Memory Size: ", len(st.session_state.knowledge_base), " characters.")
    uploaded_files = st.file_uploader("Upload EGCSE Syllabuses/Reports", accept_multiple_files=True, type=['pdf', 'txt'])
    
    if st.button("Process Documents"):
        if not api_key:
            st.error("Please provide an API Key.")
        else:
            with st.spinner("Reading EGCSE materials..."):
                st.session_state.knowledge_base = extract_text(uploaded_files)
                st.success("Knowledge Base Updated!")

# --- MAIN UI ---
st.title("🔬 EGCSE Physical Science AI Tutor")
st.caption("Official Tutor for Eswatini Form 5 Students (Subject 6888)")

MODEL_NAME = "gemini-1.5-flash"

SYSTEM_PROMPT = f"""
You are an expert Physical Science Teacher for the EGCSE (Eswatini) syllabus.
You have access to the following ECESWA materials:
{st.session_state.knowledge_base}

INSTRUCTIONS:
1. Use SI units and scientific terminology required by ECESWA.
2. If the user asks about examiner reports, reference common mistakes like 'failing to use a ruler' or 'mixing up mass and weight'.
3. Always show steps for Physics calculations (e.g., Formula -> Substitution -> Answer with Units).
4. Be encouraging to the Form 5 students.
"""

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a study question..."):
    if not api_key:
        st.error("Please enter the API Key in the sidebar.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT)
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.info("Tip: Upload your Examiner Report PDF to get specific EGCSE exam tips!")


