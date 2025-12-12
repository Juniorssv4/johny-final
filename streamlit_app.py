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

from io import BytesIO

from docx import Document

from openpyxl import load_workbook

from pptx import Presentation

# PDF support (optional)

try:

    from pdf2docx import Converter

    PDF_OK = True

except:

    PDF_OK = False

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

    "Deminer": "ນັກເກັບກູ້", "EOD": "ການທຳລາຯລະເບີດ",

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

def translate_text(text, direction):

    if not text.strip() or not model:

        return text  # Return original if no model

    glossary = get_glossary()

    target = "Lao" if direction == "English → Lao" else "English"

    prompt = f"""Expert Mine Action translator. Use exactly these terms:\n{glossary}\nTranslate to {target}. Return ONLY the translated text (no JSON).\nText: {text}"""

    try:

        r = model.generate_content(prompt)

        return r.text.strip()

    except Exception as e:

        st.error(f"Translation error: {e}")

        return text

# UI

st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")

st.title("Johny - NPA Lao Translator")

st.caption("Add to Home screen → real app")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["📄 Translate File", "✍️ Translate Text"])

with tab1:

    uploaded_file = st.file_uploader("Upload DOCX, XLSX, PPTX", type=["docx", "xlsx", "pptx"])

    if uploaded_file is not None:

        file_bytes = uploaded_file.read()

        file_name = uploaded_file.name

        ext = file_name.split('.')[-1].lower()

        if st.button("Translate File"):

            with st.spinner("Translating file..."):

                output_bytes = BytesIO()

                if ext == "docx":

                    doc = Document(BytesIO(file_bytes))

                    # Translate paragraphs

                    for p in doc.paragraphs:

                        if p.text.strip():

                            p.text = translate_text(p.text, direction)

                    # Translate tables

                    for table in doc.tables:

                        for row in table.rows:

                            for cell in row.cells:

                                for p in cell.paragraphs:

                                    if p.text.strip():

                                        p.text = translate_text(p.text, direction)

                    doc.save(output_bytes)

                elif ext == "xlsx":

                    wb = load_workbook(BytesIO(file_bytes))

                    for ws in wb.worksheets:

                        for row in ws.iter_rows():

                            for cell in row:

                                if isinstance(cell.value, str) and cell.value.strip():

                                    cell.value = translate_text(cell.value, direction)

                    wb.save(output_bytes)

                elif ext == "pptx":

                    prs = Presentation(BytesIO(file_bytes))

                    for slide in prs.slides:

                        for shape in slide.shapes:

                            if shape.has_text_frame:

                                for p in shape.text_frame.paragraphs:

                                    if p.text.strip():

                                        p.text = translate_text(p.text, direction)

                            if shape.has_table:

                                for row in shape.table.rows:

                                    for cell in row.cells:

                                        for p in cell.text_frame.paragraphs:

                                            if p.text.strip():

                                                p.text = translate_text(p.text, direction)

                    prs.save(output_bytes)

                output_bytes.seek(0)

                st.success("File translated!")

                st.download_button(

                    label="Download Translated File",

                    data=output_bytes,

                    file_name="translated_" + file_name,

                    mime="application/octet-stream"

                )

with tab2:

    text = st.text_area("Enter text", height=150)

    if st.button("Translate Text"):

        with st.spinner("Translating..."):

            result = translate_text(text, direction)

            st.success("Translation:")

            st.write(result)

# Teach term

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
 
