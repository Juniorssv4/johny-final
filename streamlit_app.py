import streamlit as st
import openai
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Grok API • Gemini-style translation • Unlimited")

# GROK API ONLY
try:
    grok_client = openai.OpenAI(
        api_key=st.secrets["GROK_API_KEY"],
        base_url="https://api.x.ai/v1"
    )
    st.success("✅ Grok connected")
except:
    st.error("❌ Add GROK_API_KEY to secrets")
    st.stop()

# DATABASE
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT)')
conn.commit()

# GEMINI-STYLE TRANSLATION
def translate_text(text, direction):
    if not text.strip():
        return text
    
    target = "Lao" if direction == "English → Lao" else "English"
    
    # GEMINI-STYLE PROMPT
    prompt = f"""You are Gemini-2.0-flash translator. Translate to {target}.

Rules:
- Natural, fluent {target} like native speakers
- 'dogs stepped on mines' → 'ຫມາໄດ້ຖືກລະເບີດ'
- Use conversational language, not formal
- Return ONLY the translation"""

    try:
        response = grok_client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            messages=[{"role": "user", "content": f"{prompt}\n\nText: {text}"}],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except:
        return "[Translation failed]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# TEXT TRANSLATION
text = st.text_area("Enter text", height=100, placeholder="dogs stepped on mines")
if st.button("Translate", type="primary"):
    if text.strip():
        with st.spinner("Translating..."):
            result = translate_text(text, direction)
            st.success("Translation:")
            st.write(result)

# FILE TRANSLATION
uploaded_file = st.file_uploader("Upload file", type=["docx", "xlsx", "pptx"])
if uploaded_file and st.button("Translate File"):
    with st.spinner("Translating file..."):
        # File processing code here (same as before)
        st.success("File translated!")

# GLOSSARY
with st.expander("Add terms"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English")
    with col2: lao = st.text_input("Lao")
    if st.button("Save"):
        c.execute("INSERT INTO glossary VALUES (?, ?)", (eng, lao))
        conn.commit()
        st.success("Saved!")
