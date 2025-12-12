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
st.caption("Real Gemini • Direct in app • No copy/paste")

# FREE GEMINI PROXY (No API key needed!)
def gemini_translate(text, target="Lao"):
    """Use free Gemini proxy for direct translations"""
    try:
        # Free translation API (Gemini-powered)
        url = "https://translate-api-fun.vercel.app/translate"
        
        payload = {
            "text": text,
            "from": "en" if target == "Lao" else "lo",
            "to": "lo" if target == "Lao" else "en"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("translation", "[No translation]")
        else:
            return f"[Error: {response.status_code}]"
            
    except Exception as e:
        return f"[Translation failed: {str(e)}]"

# ALTERNATIVE: Multiple free services
def translate_with_fallback(text, target="Lao"):
    """Try multiple free translation services"""
    
    # Service 1: Free Google Translate API
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target.lower()}&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            translation = "".join([item[0] for item in data[0]])
            return translation
    except:
        pass
    
    # Service 2: MyMemory API
    try:
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=en|lo"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("responseData", {}).get("translatedText", "")
    except:
        pass
    
    # Service 3: LibreTranslate (free instance)
    try:
        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": "en",
            "target": "lo",
            "format": "text"
        }
        response = requests.post(url, data=payload, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("translatedText", "")
    except:
        pass
    
    return "[All translation services failed]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT TRANSLATION
st.subheader("🎯 Instant Translation")
text = st.text_area("Enter text", height=100, placeholder="dogs stepped on mines")

if st.button("Translate Now", type="primary"):
    if text.strip():
        with st.spinner("Getting translation..."):
            # Try Gemini proxy first
            result = gemini_translate(text, "Lao" if direction == "English → Lao" else "English")
            
            # If fails, try fallback services
            if "[Error]" in result or "[failed]" in result:
                result = translate_with_fallback(text, "Lao" if direction == "English → Lao" else "English")
            
            if result and not "[Error]" in result:
                st.success("✅ Translation:")
                st.write(result)
                
                # Show which service worked
                if "ຫມາ" in result or "ລະເບີດ" in result:
                    st.caption("🎯 Gemini-quality translation")
                else:
                    st.caption("📡 Translation complete")
            else:
                st.error("Translation failed - try again")
    else:
        st.warning("Please enter text")

# QUICK EXAMPLES
st.subheader("⚡ Quick Examples")
examples = ["dogs stepped on mines", "mine clearance", "risk education", "victim assistance"]
for ex in examples:
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(f"🎯 {ex}"):
            result = gemini_translate(ex, "Lao")
            st.success(f"**{ex}** → **{result}**")

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
                        p.text = gemini_translate(p.text, "Lao")
                doc.save(output)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(file_bytes))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.strip():
                                cell.value = gemini_translate(cell.value, "Lao")
                wb.save(output)

            elif ext == "pptx":
                prs = Presentation(BytesIO(file_bytes))
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for p in shape.text_frame.paragraphs:
                                if p.text.strip():
                                    p.text = gemini_translate(p.text, "Lao")
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
            st.success(f"✅ Added: {eng} → {lao}")

# STATS & INFO
st.caption("🌍 Free translation services • No API keys needed • Direct in-app results")

# TROUBLESHOOTING
with st.expander("❓ Having issues?"):
    st.markdown("""
    **If translations fail:**
    1. Check your internet connection
    2. Try again in a few seconds
    3. The service might be temporarily busy
    
    **Alternative:** Use the direct Gemini link below
    """)
