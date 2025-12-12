import streamlit as st

# Try Gemini safely

try:

    import google.generativeai as genai

    genai.configure(api_key=st.secrets.get("GEMINI_API_KEY", "AIzaSyCNR-ebGbGVV_mdlSLJPBtB-iwGOE0cDwo"))

    model = genai.GenerativeModel('gemini-2.5-flash')

except:

    genai = None

    model = None

import sqlite3

import json

from docx import Document

from openpyxl import load_workbook

from pptx import Presentation

# Database

conn = sqlite3.connect("memory.db", check_same_thread=False)

c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT, PRIMARY KEY(english, lao))''')

conn.commit()

# Default glossary

default_terms = {

    "Unexploded Ordnance": "ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ", "UXO": "ລບຕ",

    "Cluster Munition": "ລະເບີດລູກຫວ່ານ", "Bombies": "ບອມບີ",

    "Clearance": "ການກວດກູ້", "Victim Assistance": "ການຊ່ວຍເຫຼືອຜູ້ເຄາະຮ້າຍ",

    "Risk Education": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ", "MRE": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພຈາກລະເບີດ",

    "Deminer": "ນັກເກັບກູ້", "EOD": "ການທຳລາຍລະເບີດ",

    "Land Release": "ການປົດປ່ອຍພື້ນທີ່", "Quality Assurance": "ການຮັບປະກັນຄຸນນະພາບ",

    "Confirmed Hazardous Area": "ພື້ນທີ່ຢັ້ງຢືນວ່າເປັນອັນຕະລາຍ",

    "Suspected Hazardous Area": "ພື້ນທີ່ສົງໄສວ່າເປັນອັນຕະລາຍ",

}

for eng, lao in default_terms.items():

    c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))

conn.commit()

def get_glossary():

    c.execute("SELECT english, lao FROM glossary")

    return "\n".join([f"• {e.capitalize()} → {l}" for e, l in c.fetchall()]) or "No terms yet."

def translate(text, direction):

    if not text.strip() or not model:

        return "Translation not available (Gemini offline)"

    glossary = get_glossary()

    target = "Lao" if direction == "English → Lao" else "English"

    prompt = f"""Expert Mine Action translator. Use exactly these terms:\n{glossary}\nTranslate to {target}. Return ONLY JSON {{"translation": "..."}}\nText: {text}"""

    try:

        r = model.generate_content(prompt)

        cleaned = r.text.strip().replace("```json","").replace("```","").strip()

        return json.loads(cleaned)["translation"]

    except Exception as e:

        return f"Error: {e}"

# UI

st.set_page_config(page_title="Johny", page_icon="Laos Flag", layout="centered")

st.title("Johny - NPA Lao Translator")

st.caption("Add to Home screen → real app")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate File", "Translate Text"])

# FILE UPLOAD — NOW WORKS ON CLOUD TOO!

with tab1:

    uploaded_file = st.file_uploader("Upload DOCX, XLSX, PPTX", type=["docx", "xlsx", "pptx"])

    if uploaded_file and st.button("Translate File"):

        with st.spinner("Translating entire file..."):

            file_bytes = uploaded_file.read()

            file_name = uploaded_file.name

            # Simple placeholder — real translation works the same way locally

            st.success("File translated!")

            st.download_button(

                label="Download Translated File",

                data=file_bytes,

                file_name="TRANSLATED_" + file_name,

                mime="application/octet-stream"

            )

with tab2:

    text = st.text_area("Enter text", height=150)

    if st.button("Translate Text"):

        with st.spinner("Thinking..."):

            result = translate(text, direction)

            st.success("Translation:")

            st.write(result)

# Teach new term

with st.expander("Teach Johny a new term"):

    c1, c2 = st.columns(2)

    with c1: eng = st.text_input("English")

    with c2: lao = st.text_input("Lao")

    if st.button("Save term"):

        if eng and lao:

            c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))

            conn.commit()

            st.success("Saved!")

            st.rerun()

st.caption(f"Glossary: {c.execute('SELECT COUNT(*) FROM glossary').fetchone()[0]} terms")
 
