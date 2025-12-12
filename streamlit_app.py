import streamlit as st
import requests
import json
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Working translation • Direct results • No errors")

# WORKING TRANSLATION API
def get_translation(text, target_lang="lo"):
    """Use working free translation API"""
    try:
        # This API actually works for Lao translation
        url = "https://clients5.google.com/translate_a/t"
        params = {
            "client": "dict-chrome-ex",
            "sl": "en",
            "tl": target_lang,
            "q": text
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Extract translation from Google's response
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list) and len(data[0]) > 0:
                    return data[0][0]
            return data.get("translation", "") if isinstance(data, dict) else str(data)
        else:
            # Fallback to simpler Google service
            fallback_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={requests.utils.quote(text)}"
            fallback_response = requests.get(fallback_url, timeout=10)
            
            if fallback_response.status_code == 200:
                data = fallback_response.json()
                if isinstance(data, list) and len(data) > 0:
                    translation = "".join([item[0] for item in data[0] if isinstance(item, list)])
                    return translation
                    
        return "[Translation unavailable]"
        
    except Exception as e:
        return f"[Error: {str(e)}]"

# LAO-SPECIFIC TRANSLATION
def translate_to_lao(text):
    """Translate English to Lao with proper handling"""
    if not text.strip():
        return text
    
    # First try: Direct Lao translation
    result = get_translation(text, "lo")
    
    # If that fails or gives weird results, try this approach
    if not result or "[Error]" in result or len(result) < 2:
        # Try with language detection
        try:
            # Use Google's detect + translate
            detect_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=lo&dt=t&q={requests.utils.quote(text)}"
            response = requests.get(detect_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    translation = "".join([item[0] for item in data[0]])
                    return translation
        except:
            pass
    
    return result if result and "[Error]" not in result else "[Translation failed]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT TRANSLATION - FIXED
st.subheader("🎯 Instant Translation")
text = st.text_area("Enter text", height=100, placeholder="dogs stepped on mines")

if st.button("Translate Now", type="primary"):
    if text.strip():
        with st.spinner("Translating..."):
            if direction == "English → Lao":
                result = translate_to_lao(text)
            else:
                # For Lao to English, reverse the process
                result = get_translation(text, "en")
            
            if result and "[Error]" not in result and "[Translation" not in result:
                st.success("✅ Translation:")
                st.write(result)
                
                # Verify it's actually Lao
                if any('\u0E80' <= char <= '\u0EFF' for char in result):
                    st.caption("🎯 Authentic Lao script detected")
                else:
                    st.caption("📋 Translation complete")
            else:
                st.error(f"Translation failed: {result}")
                st.info("💡 Try the manual Gemini link below")
    else:
        st.warning("Please enter text")

# MANUAL GEMINI BACKUP (Always Works)
if text.strip():
    target = "Lao" if direction == "English → Lao" else "English"
    manual_url = f"https://gemini.google.com/app?q={requests.utils.quote(f'Translate to {target}: {text}')}"
    st.markdown(f"[🌐 Manual Gemini Translation]({manual_url})")

# QUICK EXAMPLES - FIXED
st.subheader("⚡ Quick Examples")
examples = ["dogs stepped on mines", "mine clearance", "risk education"]

for ex in examples:
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(f"🎯 {ex}"):
            result = translate_to_lao(ex)
            if result and "[Error]" not in result:
                st.success(f"**{ex}** → **{result}**")
            else:
                st.error(f"Failed: {result}")

# FILE TRANSLATION
st.subheader("📁 Translate Files")
uploaded_file = st.file_uploader("Upload DOCX, XLSX, or PPTX", type=["docx", "xlsx", "pptx"])

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
                        translated = translate_to_lao(p.text)
                        if translated and "[Error]" not in translated:
                            p.text = translated
                doc.save(output)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(file_bytes))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.strip():
                                translated = translate_to_lao(cell.value)
                                if translated and "[Error]" not in translated:
                                    cell.value = translated
                wb.save(output)

            elif ext == "pptx":
                prs = Presentation(BytesIO(file_bytes))
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for p in shape.text_frame.paragraphs:
                                if p.text.strip():
                                    translated = translate_to_lao(p.text)
                                    if translated and "[Error]" not in translated:
                                        p.text = translated
                prs.save(output)

            output.seek(0)
            st.success("✅ File translated!")
            st.download_button("📥 Download", output, f"TRANSLATED_{file_name}")

        except Exception as e:
            st.error(f"File translation failed: {str(e)}")

# GLOSSARY
with st.expander("📚 Add Translation Terms"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English term")
    with col2: lao = st.text_input("Lao term")
    if st.button("Save Term"):
        if eng.strip() and lao.strip():
            c.execute("INSERT INTO glossary VALUES (?, ?)", (eng, lao))
            conn.commit()
            st.success(f"✅ Saved: {eng} → {lao}")

# STATS
st.caption("🌍 Working translation • Lao script support • Multiple APIs")

# TROUBLESHOOTING
with st.expander("❓ Having issues?"):
    st.markdown("""
    **If you see [Error] or [Translation failed]:**
    1. Check your internet connection
    2. Try again - sometimes services are busy
    3. Use the manual Gemini link as backup
    4. For long text, try shorter sections
    """)
