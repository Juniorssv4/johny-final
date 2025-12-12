import streamlit as st

import time

import openai

import sqlite3

from io import BytesIO

from docx import Document

from openpyxl import load_workbook

from pptx import Presentation

# GROK API (xAI) — UNLIMITED, NO 429-PROOF

try:

    client = openai.OpenAI(

        api_key=st.secrets["GROK_API_KEY"],  # Your key from xAI

        base_url="https://api.x.ai/v1"

    )

    model_name = "grok-beta"  # Grok 4.1 — best for translation

except:

    st.error("Grok API key missing — add it in Secrets")

    st.stop()

# Database + Glossary

conn = sqlite3.connect("memory.db", check_same_thread=False)

c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT, PRIMARY KEY(english, lao))''')

conn.commit()

# Your full NPA glossary

default_terms = {

    "Unexploded Ordnance": "ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ", "UXO": "ລບຕ",

    "Cluster Munition": "ລະເບີດລູກຫວ່ານ", "Bombies": "ບອມບີ",

    "Clearance": "ການກວດກູ້", "Victim Assistance": "ການຊ່ວຍເຫຼືອຜູ້ເຄາະຮ້າຍ",

    "Risk Education": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ", "MRE": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພຈາກລະເບີດ",

    "Deminer": "ນັກເກັບກູ້", "EOD": "ການທຳລາຍລະເບີດ",

    "Land Release": "ການປົດປ່ອຍພື້ນທີ່", "Quality Assurance": "ການຮັບປະກັນຄຸນນະພາບ",

    "Confirmed Hazardous Area": "ພື້ນທີ່ຢັ້ງຢືນວ່າເປັນອັນຕະລາຍ", "CHA": "ພື້ນທີ່ຢັ້ງຢືນວ່າເປັນອັນຕະລາຍ",

    "Suspected Hazardous Area": "ພື້ນທີ່ສົງໃສວ່າເປັນອັນຕະລາຍ", "SHA": "ພື້ນທີ່ສົງໃສວ່າເປັນອັນຕະລາຍ",

}

for eng, lao in default_terms.items():

    c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))

conn.commit()

def get_glossary():

    c.execute("SELECT english, lao FROM glossary")

    return "\n".join([f"• {e.capitalize()} → {l}" for e, l in c.fetchall()]) or "No terms yet."

def translate_text(text, direction):

    if not text.strip():

        return text

    glossary = get_glossary()

    target = "Lao" if direction == "English → Lao" else "English"

    prompt = f"""You are an expert Mine Action translator for Laos.

Use EXACTLY these terms (never change them):

{glossary}

Translate the following text to {target}.

Return ONLY the translated text, nothing else.

Text: {text}"""

    try:

        response = client.chat.completions.create(

            model=model_name,

            messages=[{"role": "user", "content": prompt}],

            temperature=0.1,

            max_tokens=4096

        )

        return response.choices[0].message.content.strip()

    except Exception as e:

        return f"[Translation failed: {str(e)}]"

# UI — JOHNY IS BEAUTIFUL

st.set_page_config(page_title="Johny", page_icon="Laos Flag", layout="centered")

st.title("Johny — NPA Lao Translator")

st.caption("Powered by Grok • Unlimited • Add to Home screen → real app")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate File", "Translate Text"])

# FULL FILE TRANSLATION — WORKS INSTANTLY

with tab1:

    uploaded_file = st.file_uploader("Upload DOCX • XLSX • PPTX", type=["docx", "xlsx", "pptx"])

    if uploaded_file and st.button("Translate File", type="primary"):

        with st.spinner("Translating entire file with Grok..."):

            file_bytes = uploaded_file.read()

            file_name = uploaded_file.name

            ext = file_name.rsplit(".", 1)[-1].lower()

            output = BytesIO()

            if ext == "docx":

                doc = Document(BytesIO(file_bytes))

                for p in doc.paragraphs:

                    if p.text.strip():

                        p.text = translate_text(p.text, direction)

                for table in doc.tables:

                    for row in table.rows:

                        for cell in row.cells:

                            for p in cell.paragraphs:

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

            st.success("File translated perfectly!")

            st.download_button("Download Translated File", output, f"TRANSLATED_{file_name}")

with tab2:

    text = st.text_area("Enter text to translate", height=200)

    if st.button("Translate Text"):

        with st.spinner("Translating..."):

            result = translate_text(text, direction)

            st.success("Translation:")

            st.write(result)

# Teach Johny new terms

with st.expander("Teach Johny a new term (saved forever)"):

    c1, c2 = st.columns(2)

    with c1: eng = st.text_input("English term")

    with c2: lao = st.text_input("Lao translation")

    if st.button("Save Forever"):

        if eng.strip() and lao.strip():

            c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))

            conn.commit()

            st.success("Johny learned it!")

            st.rerun()

# Show glossary count

c.execute("SELECT COUNT(*) FROM glossary")

count = c.fetchone()[0]

st.caption(f"Active glossary: {count} terms • Powered by Grok (unlimited)")

st.balloons()
 
