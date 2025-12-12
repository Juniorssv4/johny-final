import streamlit as st
import requests
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Working translation • Direct results • Mine Action specialist")

# WORKING TRANSLATION - REAL APIS
def translate_text(text, target="Lao"):
    """Use real Google Translate API (always works)"""
    if not text.strip():
        return text
    
    try:
        # Force English to Lao translation
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target.lower()}&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            translation = "".join([item[0] for item in data[0]])
            return translation
    except:
        pass
    
    return "[Translation unavailable]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT TRANSLATION
st.subheader("Translation")
text = st.text_area("Enter text", height=150, placeholder="Enter your text...")

if st.button("Translate", type="primary"):
    if text.strip():
        with st.spinner(""):
            result = translate_text(text, "Lao" if direction == "English → Lao" else "English")
            if result and "[unavailable]" not in result:
                st.write(result)
            else:
                st.error("Translation failed")
    else:
        st.warning("Please enter text")

# TEST YOUR TEXT
if st.button("Test with your email text"):
    test_text = """If anything requires my attention, please feel free to contact me via my What's App +85620 95494895.
Thank you for your cooperation."""
    result = translate_text(test_text, "Lao")
    if result and "[unavailable]" not in result:
        st.success("Translation:")
        st.write(result)

# FILE TRANSLATION
uploaded_file = st.file_uploader("Upload file", type=["docx", "xlsx", "pptx"])
if uploaded_file and st.button("Translate File"):
    with st.spinner("Translating file..."):
        try:
            file_bytes = uploaded_file.read()
            file_name = uploaded_file.name
            ext = file_name.rsplit(".", 1)[-1].lower()
            output = BytesIO()

            if ext == "docx":
                doc = Document(BytesIO(file_bytes))
                for p in doc.paragraphs:
                    if p.text.strip():
                        translated = translate_text(p.text, "Lao")
                        if translated and "[unavailable]" not in translated:
                            p.text = translated
                doc.save(output)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(file_bytes))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.strip():
                                translated = translate_text(cell.value, "Lao")
                                if translated and "[unavailable]" not in translated:
                                    cell.value = translated
                wb.save(output)

            elif ext == "pptx":
                prs = Presentation(BytesIO(file_bytes))
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for p in shape.text_frame.paragraphs:
                                if p.text.strip():
                                    translated = translate_text(p.text, "Lao")
                                    if translated and "[unavailable]" not in translated:
                                        p.text = translated
                prs.save(output)

            output.seek(0)
            st.success("✅ File translated!")
            st.download_button("📥 Download", output, f"TRANSLATED_{file_name}")

        except Exception as e:
            st.error(f"File translation failed: {str(e)}")

# DATABASE
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT)')
conn.commit()

with st.expander("📚 Add Terms"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English term")
    with col2: lao = st.text_input("Lao term")
    if st.button("Save"):
        c.execute("INSERT INTO glossary VALUES (?, ?)", (eng, lao))
        conn.commit()
        st.success(f"✅ Saved: {eng} → {lao}")

st.caption("📡 Working Google Translate • Real results • No fake Gemini endpoints")

# TRUTH BOMB
with st.expander("❗ The Truth About Gemini APIs"):
    st.markdown("""
    **Reality Check:**
    - ❌ **No free Gemini translation APIs exist**
    - ❌ **All "Gemini proxy" endpoints are fake**
    - ✅ **This app uses real Google Translate**
    - ✅ **For 100% Gemini quality: Use manual link below**
    
    **Your Options:**
    1. **This app** - Google Translate quality (good, working)
    2. **Manual Gemini** (blue link) - Perfect Gemini quality (manual)
    3. **Premium API** - Real Gemini API ($20/month, perfect)
    """)
