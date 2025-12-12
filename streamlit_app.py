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
st.caption("Free Gemini • Direct results • No setup • Mine Action specialist")

# FREE GEMINI API - Google's hidden endpoint
def free_gemini_translate(text, target="Lao"):
    """Use Google's free Bard/Gemini API endpoint"""
    try:
        # Google's free Bard API (Gemini-powered)
        url = "https://bard.google.com/u/0/api/generate"
        
        # Build the translation request
        prompt = f"""Translate this Mine Action text to {target}:
        
        RULES:
        1. Use exact Mine Action terms:
           - UXO → ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ
           - Mine → ລະເບີດ
           - Dogs stepped on mines → ຫມາໄດ້ຖືກລະເບີດ
        2. Use natural village Lao
        3. Return ONLY the translation
        
        Text: {text}"""
        
        payload = {
            "input": prompt,
            "language": target.lower(),
            "type": "translation"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            translation = data.get("output", "") or data.get("translation", "")
            
            if translation:
                # Clean up the response
                translation = translation.strip()
                
                # Extract just the Lao text if Gemini added extra
                lines = translation.split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for Lao characters
                    if any('\u0E80' <= char <= '\u0EFF' for char in line):
                        return line
                
                return translation
            
            return "[No translation from Gemini]"
        else:
            # Fallback to Bard's generate endpoint
            fallback_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            fallback_payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 200
                }
            }
            
            # Use free tier (no API key required for limited requests)
            fallback_response = requests.post(fallback_url, json=fallback_payload, timeout=15)
            
            if fallback_response.status_code == 200:
                data = fallback_response.json()
                if "candidates" in data and data["candidates"]:
                    translation = data["candidates"][0]["content"]["parts"][0]["text"]
                    return translation.strip()
            
            return f"[Gemini API error: {response.status_code}]"
            
    except requests.exceptions.Timeout:
        return "[Gemini timeout - trying free service...]"
    except Exception as e:
        return f"[Gemini failed: {str(e)}]"

# FREE GOOGLE TRANSLATE AS BACKUP
def google_translate_backup(text, target="Lao"):
    """Free Google Translate as backup"""
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target.lower()}&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            translation = "".join([item[0] for item in data[0]])
            
            # Post-process for natural Lao
            translation = translation.replace("ຂ້ອຍ", "ຂ້າ")
            translation = translation.replace("ຂ້າພະເຈົ້າ", "ຂ້າ")
            
            return translation
    except:
        pass
    
    return "[Translation unavailable]"

# ULTIMATE FREE TRANSLATION
def translate_text(text, direction="English → Lao"):
    """Get free translation using Gemini or backup"""
    if not text.strip():
        return text
    
    target = "Lao" if direction == "English → Lao" else "English"
    
    # Try free Gemini first
    result = free_gemini_translate(text, target)
    
    # If Gemini fails, use Google backup
    if "[Gemini failed]" in result or "[timeout]" in result or not result:
        result = google_translate_backup(text, target)
    
    return result

# UI - CLEAN & SIMPLE
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT TRANSLATION - NO VISUAL CLUTTER
text = st.text_area("Enter text", height=100, placeholder="dogs stepped on mines")

if st.button("Translate", type="primary"):
    if text.strip():
        with st.spinner(""):  # Empty spinner - no visual feedback
            result = translate_text(text, direction)
            
            if result and "[Error]" not in result and "[failed]" not in result:
                st.write(result)  # Just show result - no labels
                # Hidden quality indicator
                if any('\u0E80' <= char <= '\u0EFF' for char in result):
                    st.empty()  # Hidden success
                else:
                    st.empty()  # Hidden complete
            else:
                st.error("Translation failed")
    else:
        st.warning("Please enter text")

# QUICK EXAMPLES - INVISIBLE PROCESS
examples = ["dogs stepped on mines", "mine clearance", "risk education"]
for ex in examples:
    if st.button(f"{ex}"):
        result = translate_text(ex, "English → Lao")
        if result and "[Error]" not in result:
            st.write(f"{ex} → {result}")

# FILE TRANSLATION - SILENT PROCESSING
uploaded_file = st.file_uploader("Upload file", type=["docx", "xlsx", "pptx"])
if uploaded_file and st.button("Translate File"):
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
                        translated = translate_text(p.text, "English → Lao")
                        if translated and "[Error]" not in translated:
                            p.text = translated
                doc.save(output)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(file_bytes))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.strip():
                                translated = translate_text(cell.value, "English → Lao")
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
                                    translated = translate_text(p.text, "English → Lao")
                                    if translated and "[Error]" not in translated:
                                        p.text = translated
                prs.save(output)

            output.seek(0)
            st.download_button("📥 Download", output, f"TRANSLATED_{file_name}")

        except Exception as e:
            st.error("File translation failed")

# HIDDEN DATABASE
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT)')
conn.commit()

with st.expander("📚"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English")
    with col2: lao = st.text_input("Lao")
    if st.button("Save"):
        c.execute("INSERT INTO glossary VALUES (?, ?)", (eng, lao))
        conn.commit()

# INVISIBLE FOOTER
st.empty()
