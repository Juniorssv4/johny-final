import streamlit as st

import time

# Try Grok safely (xAI API)

try:

    from grok import Grok

    grok = Grok(api_key=st.secrets.get("GROK_API_KEY", "your_grok_key_here"))

    model = grok.Grok2()

except:

    grok = None

    model = None

import sqlite3

from io import BytesIO

from docx import Document

from openpyxl import load_workbook

from pptx import Presentation

# Database

conn = sqlite3.connect("memory.db", check_same_thread=False)

c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT, PRIMARY KEY(english, lao))''')

conn.commit()

# Your glossary

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

        return text

    glossary = get_glossary()

    target = "Lao" if direction == "English → Lao" else "English"

    prompt = f"""Expert Mine Action translator. Use exactly these terms:\n{glossary}\nTranslate to {target}. Return ONLY the translated text.\nText: {text}"""

    try:

        r = model.generate(prompt)

        return r.text.strip()

    except Exception as e:

        return f"Error: {e}"

# UI

st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")

st.title("Johny - NPA Lao Translator (Powered by Grok)")

st.caption("Add to Home screen → real app")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["📄 Translate File", "✍️ Translate Text"])

with tab1:

    uploaded_file = st.file_uploader("Upload DOCX / XLSX / PPTX", type=["docx", "xlsx", "pptx"])

    if uploaded_file and st.button("Translate File"):

        with st.spinner("Translating file..."):

            file_bytes = uploaded_file.read()

            file_name = uploaded_file.name

            ext = file_name.rsplit(".", 1)[-1].lower()

            output = BytesIO()

            if ext == "docx":

                doc = Document(BytesIO(file_bytes))

                for p in doc.paragraphs + [p for t in doc.tables for r in t.rows for c in r.cells for p in c.paragraphs]:

                    if p.text.strip():

                        p.text = translate_text(p.text, direction)

                doc.save(output)

            elif ext == "xlsx":

                wb = load_workbook(BytesIO(file_bytes))

                for ws in wb.worksheets:

                    for row in ws.iter_rows():

                        for cell in row:

                            if isinstance(cell.value, str) and cell.value.strip():

                                cell.value = translate_text(cell.value, direction)

                wb.save(output)

            elif ext == "pptx":

                prs = Presentation(BytesIO(file_bytes))

                for slide in prs.slides:

                    for shape in slide.shapes:

                        if shape.has_text_frame:

                            for p in shape.text_frame.paragraphs:

                                if p.text.strip():

                                    p.text = translate_text(p.text, direction)

                prs.save(output)

            output.seek(0)

            st.success("File translated successfully!")

            st.download_button("Download Translated File", output, "TRANSLATED_" + file_name)

with tab2:

    text = st.text_area("Enter text", height=150)

    if st.button("Translate Text"):

        with st.spinner("Translating..."):

            st.write(translate_text(text, direction))

# Teach term

with st.expander("Teach Johny a new term"):

    c1, c2 = st.columns(2)

    with c1: eng = st.text_input("English")

    with c2: lao = st.text_input("Lao")

    if st.button("Save"):

        if eng and lao:

            c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))

            conn.commit()

            st.success("Saved!")

            st.rerun()

st.caption(f"Glossary: {c.execute('SELECT COUNT(*) FROM glossary').fetchone()[0]} terms")
 
