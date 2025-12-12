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
st.caption("Diagnostic mode • Seeing what's happening • Forcing translation")

# DIAGNOSTIC TRANSLATION FUNCTION
def diagnose_translate(text, target="Lao"):
    """Show exactly what's happening with translation"""
    if not text.strip():
        return "[Empty text]", "[Empty text]"
    
    try:
        st.write(f"🔍 Sending text: '{text[:50]}...'")
        st.write(f"🎯 Target language: {target}")
        
        # Force English to Lao
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=lo&dt=t&q={requests.utils.quote(text)}"
        
        st.write(f"🔗 URL: {url[:100]}...")
        
        response = requests.get(url, timeout=10)
        st.write(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            st.write(f"📋 Raw response: {data}")
            
            if isinstance(data, list) and len(data) > 0:
                translation = "".join([item[0] for item in data[0]])
                st.write(f"📝 Extracted translation: '{translation}'")
                
                # Check what we got
                lao_chars = sum(1 for char in translation if '\u0E80' <= char <= '\u0EFF')
                st.write(f"🔤 Lao characters found: {lao_chars}")
                
                if lao_chars > 0:
                    return translation, f"✅ Success - {lao_chars} Lao characters"
                else:
                    return translation, "⚠️ No Lao characters detected"
            else:
                return str(data), "❌ Unexpected response format"
        else:
            return f"[HTTP {response.status_code}]", f"❌ HTTP error {response.status_code}"
            
    except Exception as e:
        return f"[Error: {str(e)}]", f"❌ Exception: {str(e)}"

# DIAGNOSTIC MODE
st.subheader("🔍 Translation Diagnostic")

text = st.text_area("Enter text", height=150, placeholder="Enter your text...")

if st.button("Diagnose Translation", type="primary"):
    if text.strip():
        result, status = diagnose_translate(text, "Lao")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Raw Result:**")
            st.write(result)
        with col2:
            st.write("**Status:**")
            st.write(status)
            
        # Try alternative approaches
        st.write("**Trying alternative approaches:**")
        
        # Method 2: Sentence by sentence
        sentences = text.split('.')
        st.write(f"Found {len(sentences)} sentences")
        
        for i, sentence in enumerate(sentences[:3]):  # First 3 sentences only
            if sentence.strip():
                sent_result, sent_status = diagnose_translate(sentence.strip(), "Lao")
                st.write(f"Sentence {i+1}: '{sentence.strip()[:50]}...' → '{sent_result[:50]}...' ({sent_status})")
        
        # Method 3: Word by word for first sentence
        if sentences:
            words = sentences[0].split()[:5]  # First 5 words
            st.write(f"First 5 words: {words}")
            for word in words:
                word_result, word_status = diagnose_translate(word, "Lao")
                st.write(f"'{word}' → '{word_result}' ({word_status})")
                
    else:
        st.warning("Please enter text")

# WORKING TRANSLATION (Simplified)
st.subheader("🔧 Working Translation")

def working_translate(text, target="Lao"):
    """Simplified but working approach"""
    try:
        # Simple approach - translate sentence by sentence
        sentences = text.split('.')
        translations = []
        
        for sentence in sentences:
            if sentence.strip():
                # Translate this sentence
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=lo&dt=t&q={requests.utils.quote(sentence.strip())}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    translation = "".join([item[0] for item in data[0]])
                    translations.append(translation)
                else:
                    translations.append(sentence.strip())  # Keep original if fails
        
        return ". ".join(translations)
    except:
        return "[Translation failed]"

if st.button("Try Working Translation"):
    if text.strip():
        result = working_translate(text, "Lao")
        st.success("Working Translation:")
        st.write(result)
        
        # Verify it's Lao
        if any('\u0E80' <= char <= '\u0EFF' for char in result):
            st.success("✅ Lao characters detected!")
        else:
            st.warning("⚠️ No Lao characters found")

# MANUAL GEMINI (Always Works)
if text.strip():
    st.subheader("🎯 Real Gemini (Manual)")
    gemini_url = f"https://gemini.google.com/app?q={requests.utils.quote(f'Translate to Lao: {text}')}"
    st.markdown(f"[🌐 Open in Real Gemini]({gemini_url})")
    result = st.text_area("Copy Gemini translation here:", height=100)
    if result.strip():
        st.success("Real Gemini Translation:")
        st.write(result)

# DATABASE
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

st.caption("🔍 Diagnostic mode • Seeing what's happening • Finding the real solution")
