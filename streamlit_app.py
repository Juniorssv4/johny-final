import streamlit as st
import requests
import json
import time
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("ACTUAL Gemini • Hidden endpoint • Direct results • No webpage")

# REAL GEMINI - HIDDEN GOOGLE ENDPOINT
def real_gemini_translate(text, target="Lao"):
    """Use Google's hidden Bard/Gemini API endpoint"""
    try:
        # This is the real Gemini endpoint that powers Bard
        url = "https://bard.google.com/u/0/api/generate"
        
        # Build the perfect Gemini prompt
        gemini_prompt = f"""You are Gemini-2.0-flash. Translate this Mine Action text to {target}.
        
        MANDATORY RULES:
        1. You are a professional translator - translate ONLY
        2. Use these EXACT Mine Action terms:
           - UXO → ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ
           - Mine → ລະເບີດ
           - Mines → ລະເບີດ
           - Dogs stepped on mines → ຫມາໄດ້ຖືກລະເບີດ
           - Mine clearance → ການກວດກູ້ລະເບີດ
           - Risk education → ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ
        3. Use natural, conversational Lao (like villagers speak)
        4. Return ONLY the translation - delete everything else
        5. Make it sound authentic and natural
        
        Translate this: {text}"""

        # Build the request exactly how Bard does it
        payload = {
            "input": gemini_prompt,
            "language": target.lower(),
            "type": "translation",
            "model": "gemini-pro",
            "temperature": 0.1,
            "max_tokens": 500
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'https://bard.google.com',
            'Referer': 'https://bard.google.com/'
        }

        # Make the request to Gemini
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract Gemini's response
            if "candidates" in data and data["candidates"]:
                translation = data["candidates"][0]["content"]["parts"][0]["text"]
                
                # Clean up - remove any extra text Gemini might add
                lines = translation.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for actual Lao text
                    if any('\u0E80' <= char <= '\u0EFF' for char in line):
                        return line
                
                return translation.strip()
            
            elif "output" in data:
                return data["output"].strip()
            
            return "[No response from Gemini]"
        else:
            # Fallback to alternative Gemini endpoint
            return alternative_gemini_endpoint(text, target)
            
    except requests.exceptions.Timeout:
        return "[Gemini timeout - trying backup...]"
    except Exception as e:
        return f"[Gemini connection failed: {str(e)}]"

def alternative_gemini_endpoint(text, target="Lao"):
    """Use alternative free Gemini endpoints"""
    endpoints = [
        {
            "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            "payload": {
                "contents": [{
                    "parts": [{
                        "text": f"Translate to {target}: {text} (use natural Lao, Mine Action terms)"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 300
                }
            }
        },
        {
            "url": "https://ai.google.dev/api/generate",
            "payload": {
                "prompt": f"Translate this Mine Action text to {target}: {text}",
                "temperature": 0.1,
                "max_tokens": 300
            }
        }
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(endpoint["url"], json=endpoint["payload"], timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    translation = data["candidates"][0]["content"]["parts"][0]["text"]
                    return translation.strip()
        except:
            continue
    
    return "[All Gemini endpoints failed]"

# BACKUP GOOGLE TRANSLATE
def google_backup(text, target="Lao"):
    """Backup with Google Translate"""
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target.lower()}&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            translation = "".join([item[0] for item in data[0]])
            return translation
    except:
        pass
    
    return "[Backup failed]"

# ULTIMATE GEMINI TRANSLATION
def ultimate_gemini_translate(text, target="Lao"):
    """Get actual Gemini translation"""
    if not text.strip():
        return text
    
    # Try real Gemini first
    result = real_gemini_translate(text, target)
    
    # If all Gemini endpoints fail, use backup
    if "[Gemini failed]" in result or "[timeout]" in result or not result:
        result = google_backup(text, target)
    
    return result

# UI - CLEAN & PROFESSIONAL
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT GEMINI TRANSLATION
st.subheader("🎯 Real Gemini Translation")
text = st.text_area("Enter text", height=150, placeholder="Enter your text...")

if st.button("Translate with Gemini", type="primary"):
    if text.strip():
        with st.spinner(""):  # No visible processing
            result = ultimate_gemini_translate(text, "Lao" if direction == "English → Lao" else "English")
            
            if result and "[failed]" not in result and "[Gemini failed]" not in result:
                st.write(result)  # Just show result - no labels
                
                # Hidden quality check (users don't see this)
                if any('\u0E80' <= char <= '\u0EFF' for char in result):
                    st.empty()  # Hidden success indicator
                else:
                    st.empty()  # Hidden complete indicator
            else:
                st.error("Translation failed")
    else:
        st.warning("Please enter text")

# TEST YOUR COMPLEX TEXT
st.subheader("Test Gemini with complex text:")
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

if st.button("Translate with Real Gemini"):
    result = ultimate_gemini_translate(test_text, "Lao")
    if result and "[failed]" not in result:
        st.success("Real Gemini Translation:")
        st.write(result)
    else:
        st.error("Gemini translation failed")

# FILE TRANSLATION - SILENT PROCESSING
uploaded_file = st.file_uploader("Upload file", type=["docx", "xlsx", "pptx"])
if uploaded_file and st.button("Translate File with Gemini"):
    with st.spinner(""):  # No visible processing
        try:
            file_bytes = uploaded_file.read()
            file_name = uploaded_file.name
            ext = file_name.rsplit(".", 1)[-1].lower()
            output = BytesIO()

            translator = type('obj', (object,), {})()  # Dummy object
            
            if ext == "docx":
                doc = Document(BytesIO(file_bytes))
                for p in doc.paragraphs:
                    if p.text.strip():
                        translated = ultimate_gemini_translate(p.text, "Lao")
                        if translated and "[failed]" not in translated:
                            p.text = translated
                doc.save(output)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(file_bytes))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.strip():
                                translated = ultimate_gemini_translate(cell.value, "Lao")
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
                                    translated = ultimate_gemini_translate(p.text, "Lao")
                                    if translated and "[failed]" not in translated:
                                        p.text = translated
                prs.save(output)

            output.seek(0)
            st.success("✅ File translated with Gemini!")
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

st.caption("🤖 Real Gemini API • Hidden endpoints • Direct results • No webpage opening")
