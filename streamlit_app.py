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
st.caption("Train Gemini web • Mine Action specialist • No opinions")

# TRAINED GEMINI PROMPT BUILDER
def build_gemini_prompt(text, direction="English → Lao"):
    """Build training prompt for Gemini web interface"""
    
    target = "Lao" if direction == "English → Lao" else "English"
    
    return f"""You are Johny, a Mine Action translator. Your ONLY job is translation.

MANDATORY RULES:
1. Translate EXACTLY what's requested - no opinions, explanations, or extra text
2. Use these EXACT Mine Action terms:
   - UXO → ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ
   - Mine → ລະເບີດ  
   - Mine clearance → ການກວດກູ້ລະເບີດ
   - Dogs stepped on mines → ຫມາໄດ້ຖືກລະເບີດ
   - Risk education → ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ
   - Unexploded ordnance → ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ
   - Cluster munition → ລະເບີດລູກຫວ່ານ
   - Clearance → ການກວດກູ້
   - Victim assistance → ການຊ່ວຍເຫຼືອຜູ້ເຄາະຮ້າຍ

3. Use natural village Lao (conversational, not formal)
4. Return ONLY the translation - delete everything else

CRITICAL: Translate this exact text to {target} and return ONLY the translation:
{text}"""

# INSTANT GEMINI ACCESS
st.subheader("🎯 Train Gemini Web")
text = st.text_area("1. Enter your text", height=100, placeholder="dogs stepped on mines")

if text.strip():
    # Build trained prompt
    trained_prompt = build_gemini_prompt(text)
    
    # Create Gemini link with training
    gemini_url = f"https://gemini.google.com/app?q={requests.utils.quote(trained_prompt)}"
    
    st.markdown(f"[🌐 2. Click here to open trained Gemini]({gemini_url})")
    st.caption("This opens Gemini with your trained prompt ready")
    
    # Result input
    result = st.text_area("3. Copy Gemini's translation and paste here:", height=100)
    
    if result.strip():
        st.success("✅ Your Trained Gemini Translation:")
        st.write(result)
        
        # Verify it's trained properly
        if len(result.split()) <= 10:  # Gemini should give concise translation
            st.caption("🎯 Gemini followed training - concise translation")
        else:
            st.caption("📋 Translation received - you may need to retrain Gemini")

# QUICK TRAINED EXAMPLES
st.subheader("⚡ Trained Examples")
examples = ["dogs stepped on mines", "mine clearance operations", "risk education for children"]

for ex in examples:
    trained_ex = build_gemini_prompt(ex)
    url = f"https://gemini.google.com/app?q={requests.utils.quote(trained_ex)}"
    st.markdown(f"[🎯 {ex}]({url})")

# GEMINI TRAINING TIPS
with st.expander("📚 How to Train Gemini Perfectly"):
    st.markdown("""
    **Training Steps:**
    1. **Copy the exact prompt** from step 2
    2. **Click the Gemini link** 
    3. **If Gemini adds extra text**, tell it: "Translate only, no extra text"
    4. **Copy just the translation** (ignore explanations)
    
    **If Gemini misbehaves:**
    - Say: "You are a translator only. Translate exactly: [text]"
    - Or refresh and try again
    
    **Perfect Training Prompt:**
    ```
    You are a translator. Translate to Lao: [text]. Return ONLY translation.
    ```
    """)

# FILE TRANSLATION WITH TRAINING
st.subheader("📁 Translate Files")
uploaded_file = st.file_uploader("Upload DOCX, XLSX, or PPTX", type=["docx", "xlsx", "pptx"])

if uploaded_file:
    st.write("**File Translation Steps:**")
    st.write("1. Download your file")
    st.write("2. Copy text sections")
    st.write("3. Use trained Gemini links above")
    st.write("4. Replace with translations")

# DATABASE
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT)')
conn.commit()

with st.expander("📚 Add Terms"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English")
    with col2: lao = st.text_input("Lao")
    if st.button("Save"):
        c.execute("INSERT INTO glossary VALUES (?, ?)", (eng, lao))
        conn.commit()
        st.success(f"✅ Saved: {eng} → {lao}")

st.caption("🎯 Train Gemini to be your dedicated Mine Action translator • No opinions • Just translations")
