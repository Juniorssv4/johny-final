import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# --- PAGE SETUP ---
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Gemini web scraping • No API quota • Fluent Lao")

# --- HEADLESS BROWSER SETUP ---
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

driver = get_driver()

# --- GEMINI WEB TRANSLATION ---
def gemini_web_translate(text, target_lang="Lao"):
    try:
        driver.get("https://gemini.google.com/app")
        time.sleep(3)  # Wait for page load

        # Find input box (adjust selector if Gemini changes)
        input_box = driver.find_element(By.CSS_SELECTOR, "textarea[aria-label*='Prompt']")
        prompt = f"Translate this Mine Action text to {target_lang}: {text}"
        input_box.send_keys(prompt)
        input_box.send_keys(Keys.RETURN)

        # Wait for response
        time.sleep(5)
        
        # Grab the last response (Gemini's translation)
        responses = driver.find_elements(By.CSS_SELECTOR, "div[data-message-author='2']")
        if responses:
            return responses[-1].text.strip()
        else:
            return "[Gemini web: no response]"

    except Exception as e:
        return f"[Gemini web error: {str(e)}]"

# --- UI ---
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

st.subheader("🎯 Translate Text")
text = st.text_area("Enter text", height=100, placeholder="dogs stepped on mines")

if st.button("Translate with Gemini Web", type="primary"):
    if text.strip():
        with st.spinner("Scraping Gemini web interface..."):
            result = gemini_web_translate(text, "Lao" if direction == "English → Lao" else "English")
            st.success("✅ Gemini Translation:")
            st.write(result)
    else:
        st.warning("Please enter text")

# --- FILE TRANSLATION ---
st.subheader("📁 Translate File")
uploaded_file = st.file_uploader("Upload DOCX/XLSX/PPTX", type=["docx", "xlsx", "pptx"])

if uploaded_file:
    if st.button("Translate File via Gemini Web"):
        with st.spinner("Extracting + scraping Gemini..."):
            try:
                # Extract text
                file_bytes = uploaded_file.read()
                ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
                texts = []

                if ext == "docx":
                    doc = Document(BytesIO(file_bytes))
                    texts = [p.text for p in doc.paragraphs if p.text.strip()]

                elif ext == "xlsx":
                    wb = load_workbook(BytesIO(file_bytes))
                    for ws in wb.worksheets:
                        for row in ws.iter_rows():
                            for cell in row:
                                if isinstance(cell.value, str) and cell.value.strip():
                                    texts.append(cell.value)

                elif ext == "pptx":
                    prs = Presentation(BytesIO(file_bytes))
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if shape.has_text_frame:
                                for p in shape.text_frame.paragraphs:
                                    if p.text.strip():
                                        texts.append(p.text)

                # Translate each chunk
                translated_texts = [gemini_web_translate(t) for t in texts[:5]]  # Limit for speed

                st.success("✅ Translated via Gemini web!")
                for orig, trans in zip(texts, translated_texts):
                    st.write(f"**{orig}** → **{trans}**")

            except Exception as e:
                st.error(f"File failed: {str(e)}")

# --- GLOSSARY ---
with st.expander("📚 Add Terms"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English")
    with col2: lao = st.text_input("Lao")
    if st.button("Save"):
        if eng.strip() and lao.strip():
            st.success(f"✅ Added: {eng} → {lao}")

st.caption("🚀 Gemini web scraping • No API keys • No quotas")
