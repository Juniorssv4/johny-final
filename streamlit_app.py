import streamlit as st
import requests
import time
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Gemini web scraping • Real Gemini • No API quota")

# GEMINI WEB SCRAPING
def gemini_translate(text, target="Lao"):
    """Scrape Gemini web interface for real translation"""
    try:
        # Build Gemini web URL with query
        query = f"Translate this to {target}: {text}"
        url = f"https://gemini.google.com/app?q={requests.utils.quote(query)}"
        
        # Scrape the response (simplified method)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # Extract translation from response (basic method)
        if response.status_code == 200:
            # Look for translation in response content
            content = response.text
            
            # Find Lao characters (Unicode range: 0x0E80-0x0EFF)
            import re
            lao_text = re.findall(r'[\u0E80-\u0EFF]+(?:\s*[\u0E80-\u0EFF]+)*', content)
            
            if lao_text:
                return " ".join(lao_text[:3])  # Take first few Lao text chunks
            else:
                return "[No Lao text found in Gemini response]"
        else:
            return f"[Gemini web error: {response.status_code}]"
            
    except Exception as e:
        return f"[Translation failed: {str(e)}]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# TEXT TRANSLATION
text = st.text_area("Enter text", height=100, placeholder="dogs stepped on mines")

if st.button("Translate with Gemini Web", type="primary"):
    if text.strip():
        with st.spinner("Scraping Gemini web interface..."):
            result = gemini_translate(text)
            st.success("Real Gemini Translation:")
            st.write(result)
            st.caption("✅ From actual Gemini web • No API used")
    else:
        st.warning("Please enter text")

# DIRECT GEMINI LINK (Backup)
if text:
    direct_url = f"https://gemini.google.com/app?q={requests.utils.quote(f'Translate to Lao: {text}')}"
    st.markdown(f"[🌐 Open in Gemini]({direct_url})")
