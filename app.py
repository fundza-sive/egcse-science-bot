import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- PERSISTENT KNOWLEDGE CACHING ---
# This decorator tells Streamlit to keep this data in memory even if the page refreshes
@st.cache_resource(show_spinner="Loading EGCSE Knowledge Base...")
def process_knowledge_base(files):
    text_content = ""
    if not files:
        return ""
    for file in files:
        try:
            if file.type == "application/pdf":
                reader = PdfReader(file)
                text_content += f"\n--- {file.name} ---\n"
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
            else:
                text_content += f"\n--- {file.name} ---\n"
                text_content += file.read().decode("utf-8")
        except Exception as e:
            text_content += f"\n(Error reading {file.name})\n"
    return text_content

# --- CONFIGURATION ---
st.set_page_config(page_title="EGCSE Physical Science Tutor", page_icon="🔬", layout="wide")

# Initialize Chat History (This stays for the current tab session)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Teacher Dashboard")
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Enter Gemini API Key:", type="password")
    
    st.markdown("---")
    st.subheader("📚 Upload Materials")
    uploaded_files = st.file_uploader("Upload EGCSE PDFs", accept_multiple_files=True, type=['pdf', 'txt'])
    
    # Store the processed text in a global cache
    if st.button("Save to Bot Memory"):
        if not api_key:
            st.error("Missing API Key")
        else:
            knowledge_text = process_knowledge_base(uploaded_files)
            st.session_state['kb_text'] = knowledge_text
            st.success("Documents locked into memory!")

# Retrieve the knowledge from state or cache
knowledge_base = st.session_state.get('kb_text', "")

# --- MAIN UI ---
st.title("🔬 EGCSE Physical Science AI Tutor")
st.caption("Eswatini Form 5 Study Tool (Subject 6888)")

SYSTEM_PROMPT = f"""
You are an expert Physical Science Teacher for the EGCSE (Eswatini) syllabus.
Knowledge Base Content:
{knowledge_base}

Always use step-by-step Physics logic and ECESWA terminology.
"""

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about the syllabus or a past paper..."):
    if not api_key:
        st.error("Please enter the API Key in the sidebar.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Error: {str(e)}")

