import streamlit as st
import time
import google.generativeai as genai
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

# GEMINI CONFIG
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Add GEMINI_API_KEY in Secrets")
    st.stop()

# Primary and fallback models
PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-1.5-flash"

if "current_model" not in st.session_state:
    st.session_state.current_model = PRIMARY_MODEL

model = genai.GenerativeModel(st.session_state.current_model)

# Backoff
@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def safe_generate_content(prompt):
    return model.generate_content(prompt)

# Glossary from repo file
GLOSSARY_FILE = "glossary.txt"

if "glossary" not in st.session_state:
    try:
        import requests
        raw_url = "https://raw.githubusercontent.com/Juniorssv4/johny-final/main/glossary.txt"
        response = requests.get(raw_url)
        lines = response.text.splitlines()
        glossary_dict = {}
        for line in lines:
            if ":" in line:
                eng, lao = line.strip().split(":", 1)
                glossary_dict[eng.strip().lower()] = lao.strip()
        st.session_state.glossary = glossary_dict
    except:
        st.session_state.glossary = {}

glossary = st.session_state.glossary

def get_glossary_prompt():
    if glossary:
        terms = "\n".join([f"• {e.capitalize()} → {l}" for e, l in glossary.items()])
        return f"Use EXACTLY these terms:\n{terms}\n"
    return ""

# Translate function same as before
def translate_text(text, direction):
    if not text.strip():
        return text
    target = "Lao" if direction == "English → Lao" else "English"
    prompt = f"""{get_glossary_prompt()}Translate ONLY the text to {target}.
Return ONLY the translation.

Text: {text}"""

    try:
        response = safe_generate_content(prompt)
        return response.text.strip()
    except RetryError as e:
        if "429" in str(e.last_attempt.exception()) or "quota" in str(e.last_attempt.exception()).lower():
            if st.session_state.current_model == PRIMARY_MODEL:
                st.session_state.current_model = FALLBACK_MODEL
                st.info("Rate limit on gemini-2.5-flash — switched to gemini-1.5-flash.")
                global model
                model = genai.GenerativeModel(FALLBACK_MODEL)
                response = model.generate_content(prompt)
                return response.text.strip()
        st.error("Timed out after retries — try again in 5 minutes.")
        return "[Failed — try later]"
    except Exception as e:
        st.error(f"API error: {str(e)}")
        return "[Failed — try again]"

# UI same
st.set_page_config(
    page_title="Johny",
    page_icon="https://raw.githubusercontent.com/Juniorssv4/johny-final/main/Johny.png",
    layout="centered"
)
st.title("😊 Johny — NPA Lao Translator")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate Text", "Translate File"])

# Your file translation code here (same as before)

# Teach term — shows message to edit in GitHub
with st.expander("➕ Teach Johny a new term (edit glossary.txt in GitHub)"):
    st.info("To add term: Edit glossary.txt in GitHub repo → add line 'english:lao' → save → reboot app.")
    st.code("Example:\nSamir:ສະຫມີຣ\nhello:ສະບາຍດີ")

st.caption(f"Active glossary: {len(glossary)} terms • Model: {st.session_state.current_model}")
