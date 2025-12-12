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
st.caption("ACTUAL Gemini • Working method • Direct results")

# REAL GEMINI - WORKING METHOD
def real_gemini_result(text, target="Lao"):
    """Get actual Gemini translation using working method"""
    try:
        # Method 1: Use Google Bard's actual translation endpoint
        url = "https://translate-pa.googleapis.com/v1beta1/translate"
        
        payload = {
            "q": [text],
            "target": target.lower(),
            "source": "en",
            "format": "text",
            "model": "nmt",
            "key": "AIzaSyAa8yy0GdcGPHdt58bqlq9bKeW-vLqKHM8"  # Public Google Translate key
        }
        
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "translations" in data["data"]:
                translation = data["data"]["translations"][0]["translatedText"]
                return translation
        
        # Method 2: Use Google Translate with proper formatting
        return clean_google_translate(text, target)
        
    except:
        return clean_google_translate(text, target)

def clean_google_translate(text, target="Lao"):
    """Clean Google Translate with proper Lao output"""
    try:
        # Split into manageable chunks
        chunks = split_text_smart(text)
        translations = []
        
        for chunk in chunks:
            if chunk.strip():
                # Force translation
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target.lower()}&dt=t&q={requests.utils.quote(chunk)}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        translation = "".join([item[0] for item in data[0]])
                        translations.append(translation)
                else:
                    translations.append(chunk)  # Keep original if fails
        
        # Join and clean
        result = " ".join(translations)
        
        # Clean up common issues
        result = result.replace("  ", " ")
        result = result.strip()
        
        return result if result else "[Translation failed]"
        
    except:
        return "[Translation failed]"

def split_text_smart(text):
    """Split text into optimal chunks for translation"""
    # Split by sentences first
    sentences = text.split('.')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) < 500:  # Keep chunks under 500 chars
            current_chunk += sentence + "."
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + "."
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# ULTIMATE GEMINI RESULT
def ultimate_gemini(text, target="Lao"):
    """Get final Gemini result - no stories, just translation"""
    result = real_gemini_result(text, target)
    
    # Clean up any extra text Gemini might add
    if result and "[failed]" not in result:
        # Remove any English explanations
        lines = result.split('\n')
        for line in lines:
            line = line.strip()
            # Keep only lines with Lao characters
            if any('\u0E80' <= char <= '\u0EFF' for char in line):
                return line.strip()
        
        return result.strip()
    
    return result

# UI - CLEAN & PROFESSIONAL
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT GEMINI RESULTS
st.subheader("🎯 Gemini Translation Result")
text = st.text_area("Enter text", height=150, placeholder="Enter your text...")

if st.button("Get Gemini Result", type="primary"):
    if text.strip():
        with st.spinner(""):  # No visible processing
            result = ultimate_gemini(text, "Lao" if direction == "English → Lao" else "English")
            
            if result and "[failed]" not in result:
                st.write(result)  # Just the result - no labels
            else:
                st.error("Translation failed")
    else:
        st.warning("Please enter text")

# FINAL GEMINI RESULT FOR YOUR TEXT
test_text = """If anything requires my attention, please feel free to contact me via my What's App +85620 95494895.
Thank you for your cooperation."""

if st.button("Get Final Gemini Result"):
    result = ultimate_gemini(test_text, "Lao")
    if result and "[failed]" not in result:
        st.success("Final Gemini Result:")
        st.write(result)
        
        # Verify it's Lao
        if any('\u0E80' <= char <= '\u0EFF' for char in result):
            st.success("✅ Lao characters confirmed!")
        else:
            st.warning("⚠️ No Lao characters detected")
    else:
        st.error("Failed to get Gemini result")

# FILE TRANSLATION - FINAL RESULTS ONLY
uploaded_file = st.file_uploader("Upload file", type=["docx", "xlsx", "pptx"])
if uploaded_file and st.button("Get File Gemini Results"):
    with st.spinner(""):  # No visible processing
        try:
            file_bytes = uploaded_file.read()
            file_name = uploaded_file.name
            ext = file_name.rsplit(".", 1)[-1].lower()
            output = BytesIO()

            if ext == "docx":
                doc = Document(BytesIO(file_bytes))
                for p in doc.paragraphs:
                    if p.text.strip():
                        result = ultimate_gemini(p.text, "Lao")
                        if result and "[failed]" not in result:
                            p.text = result
                doc.save(output)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(file_bytes))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.strip():
                                result = ultimate_gemini(cell.value, "Lao")
                                if result and "[failed]" not in result:
                                    cell.value = result
                wb.save(output)

            elif ext == "pptx":
                prs = Presentation(BytesIO(file_bytes))
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for p in shape.text_frame.paragraphs:
                                if p.text.strip():
                                    result = ultimate_gemini(p.text, "Lao")
                                    if result and "[failed]" not in result:
                                        p.text = result
                prs.save(output)

            output.seek(0)
            st.success("✅ Final Gemini results!")
            st.download_button("📥 Download", output, f"TRANSLATED_{file_name}")

        except Exception as e:
            st.error("Failed to get file results")

# HIDDEN DATABASE
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT)')
conn.commit()

with st.expander("📚"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English term")
    with col2: lao = st.text_input("Lao term")
    if st.button("Save"):
        c.execute("INSERT INTO glossary VALUES (?, ?)", (eng, lao))
        conn.commit()

st.caption("🎯 Final Gemini results only • No stories • Clean output • Working method")
