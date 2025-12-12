import streamlit as st

# --- Try to import Gemini (works on your PC, safe fallback on Streamlit Cloud) ---

try:

    import google.generativeai as genai

except ImportError:

    genai = None

    st.error("Gemini not available on this server — contact admin to install google-generativeai package")

import sqlite3

import json

import os

from docx import Document

from openpyxl import load_workbook

from pptx import Presentation

# Gemini key (will use Secrets if available, otherwise your key)

if genai:

    api_key = st.secrets.get("GEMINI_API_KEY", "AIzaSyCNR-ebGbGVV_mdlSLJPBtB-iwGOE0cDwo")

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-2.5-flash')

# Database

conn = sqlite3.connect("memory.db", check_same_thread=False)

c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT, PRIMARY KEY(english, lao))''')

conn.commit()

# Default terms

default_terms = {

    "Unexploded Ordnance": "ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ", "UXO": "ລບຕ",

    "Cluster Munition": "ລະເບີດລູກຫວ່ານ", "Bombies": "ບອມບີ",

    "Clearance": "ການກວດກູ້", "Victim Assistance": "ການຊ່ວຍເຫຼືອຜູ້ເຄາະຮ້າຍ",

    "Risk Education": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ", "MRE": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພຈາກລະເບີດ",

    "Deminer": "ນັກເກັບກູ້", "EOD": "ການທຳລາຍລະເບີດ",

    "Land Release": "ການປົດປ່ອຍພື້ນທີ່", "Quality Assurance": "ການຮັບປະກັນຄຸນນະພາບ",

    "Confirmed Hazardous Area": "ພື້ນທີ່ຢັ້ງຢືນວ່າເປັນອັນຕະລາຍ",

    "Suspected Hazardous Area": "ພື້ນທີ່ສົງໃສວ່າເປັນອັນຕະລາຍ",

}

for eng, lao in default_terms.items():

    c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))

conn.commit()

def get_glossary():

    c.execute("SELECT english, lao FROM glossary")

    return "\n".join([f"• {e.capitalize()} → {l}" for e, l in c.fetchall()]) or "No terms yet."

def translate(text, direction):

    if not text.strip() or not genai:

        return "Translation unavailable"

    glossary = get_glossary()

    target = "Lao" if direction == "English → Lao" else "English"

    prompt = f"""Expert Mine Action translator. Use exactly these terms:\n{glossary}\nTranslate to {target}. Return ONLY JSON {{"translation": "..."}}\nText: {text}"""

    try:

        r = model.generate_content(prompt)

        cleaned = r.text.strip().replace("```json", "").replace("```", "")

        return json.loads(cleaned)["translation"]

    except Exception as e:

        return f"Error: {e}"

# UI

st.set_page_config(page_title="Johny", page_icon="Laos Flag", layout="centered")

st.title("Johny - NPA Lao Translator")

st.caption("Add to Home screen for real app experience")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate File", "Translate Text"])

with tab1:

    st.info("File upload coming soon — works perfectly on local version")

with tab2:

    text = st.text_area("Enter text", height=150)

    if st.button("Translate"):

        with st.spinner("Thinking..."):

            result = translate(text, direction)

            st.success("Translation:")

            st.write(result)

# Teach term

with st.expander("Teach Johny a new term"):

    c1, c2 = st.columns(2)

    with c1: eng = st.text_input("English")

    with c2: lao = st.text_input("Lao")

    if st.button("Save"):

        if eng and lao:

            c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))

            conn.commit()

            st.success("Learned!")

            st.rerun()

st.caption(f"Glossary has {c.execute('SELECT COUNT(*) FROM glossary').fetchone()[0]} terms")
For Sale Page
 
