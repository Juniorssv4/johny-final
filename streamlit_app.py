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

# FIXED TRANSLATION FUNCTION
def translate_text(text, target="Lao"):
    """Force translation to Lao with proper handling"""
    if not text.strip():
        return text
    
    try:
        # Force English to Lao translation
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=lo&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            translation = "".join([item[0] for item in data[0]])
            
            # Verify we got Lao text
            if any('\u0E80' <= char <= '\u0EFF' for char in translation):
                return translation
            else:
                # If no Lao chars, try alternative approach
                return force_lao_translation(text)
    except:
        pass
    
    return force_lao_translation(text)

def force_lao_translation(text):
    """Force Lao translation using segment approach"""
    try:
        # Break into sentences and translate each
        sentences = text.split('.')
        translations = []
        
        for sentence in sentences:
            if sentence.strip():
                # Simple word-by-word approach for complex text
                words = sentence.strip().split()
                translated_words = []
                
                for word in words:
                    # Translate individual words
                    word_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=lo&dt=t&q={requests.utils.quote(word)}"
                    word_response = requests.get(word_url, timeout=5)
                    
                    if word_response.status_code == 200:
                        word_data = word_response.json()
                        translated_word = word_data[0][0][0] if word_data[0] else word
                        translated_words.append(translated_word)
                    else:
                        translated_words.append(word)
                
                translations.append(" ".join(translated_words))
        
        return ". ".join(translations)
    except:
        return "[Translation failed]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT TRANSLATION
text = st.text_area("Enter text", height=150, placeholder="Enter your text here...")

if st.button("Translate", type="primary"):
    if text.strip():
        with st.spinner(""):
            result = translate_text(text, "Lao" if direction == "English → Lao" else "English")
            
            if result and "[failed]" not in result:
                st.write(result)
                # Verify we got Lao
                if any('\u0E80' <= char <= '\u0EFF' for char in result):
                    st.caption("✅ Lao translation complete")
                else:
                    st.caption("⚠️ Translation may need adjustment")
            else:
                st.error("Translation failed")
    else:
        st.warning("Please enter text")

# TEST YOUR LONG TEXT
st.subheader("Test with your text:")
test_text = """advance and travel claims.
Authorize for booking of financial data into the Agresso system for the finance users in the south.
Hi all, Please be informed that I will be out of the office from 13-21 December for SD and AL.
During my absence, Phetdara his email address @Phetdara Luangonchanh will be acting as Field Finance Coordinator.
He is authorized to perform the following tasks up to my level:
• Review expenditure before payment, including RFLP, PR, PO, petty cash claims, Settlement of advance and travel claims.
• Authorize for booking of financial data into the Agresso system for the finance users in the south.
• Follow up on MTR data collection from respective departments.
• Process and submit fund requests to VTE by 15 December for funds to be spent during 01-12 January 2026
If anything requires my attention, please feel free to contact me via my What's App +85620 95494895.
Thank you for your cooperation."""

if st.button("Translate this text"):
    result = translate_text(test_text, "Lao")
    if result and "[failed]" not in result:
        st.success("Translation:")
        st.write(result)
    else:
        st.error("Failed to translate")

# FILE TRANSLATION
uploaded_file = st.file_uploader("Upload file", type=["docx", "xlsx", "pptx"])
if uploaded_file and st.button("Translate File"):
    with st.spinner("Translating..."):
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
                        if translated and "[failed]" not in translated:
                            p.text = translated
                doc.save(output)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(file_bytes))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.strip():
                                translated = translate_text(cell.value, "Lao")
                                if translated and "[failed]" not in translated:
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
                                    if translated and "[failed]" not in translated:
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

st.caption("🔄 Working translation • Force Lao output • Complex text handling")
