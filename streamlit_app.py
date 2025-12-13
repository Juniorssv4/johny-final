import streamlit as st

import time

import google.generativeai as genai

import sqlite3

from io import BytesIO

from docx import Document

from openpyxl import load_workbook

from pptx import Presentation

# GEMINI ONLY — SECURE + PROGRESS BAR

try:

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    model = genai.GenerativeModel("gemini-2.5-flash")

except:

    st.error("Gemini API key not found — add GEMINI_API_KEY in Secrets")

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

Make it fluent, natural, and idiomatic — like a native speaker.

Return ONLY the translated text, nothing else.

Text: {text}"""

    for attempt in range(6):

        try:

            response = model.generate_content(prompt)

            return response.text.strip()

        except Exception as e:

            if "429" in str(e) or "quota" in str(e).lower():

                wait = 40 + attempt * 10

                st.toast(f"Rate limit — waiting {wait}s...")

                time.sleep(wait)

            else:

                return f"[Error: {e}]"

    return "[Translation timed out]"

# UI

st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")

st.title("Johny — NPA Lao Translator")

st.caption("Pure Gemini quality • Progress bar • Add to Home screen = real app")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate File", "Translate Text"])

with tab1:

    uploaded_file = st.file_uploader("Upload DOCX • XLSX • PPTX", type=["docx", "xlsx", "pptx"])

    if uploaded_file and st.button("Translate File", type="primary"):

        with st.spinner("Translating file with Gemini..."):

            file_bytes = uploaded_file.read()

            file_name = uploaded_file.name

            ext = file_name.rsplit(".", 1)[-1].lower()

            output = BytesIO()

            # Collect all text elements for progress bar

            text_elements = []

            if ext == "docx":

                doc = Document(BytesIO(file_bytes))

                for p in doc.paragraphs:

                    if p.text.strip():

                        text_elements.append(("doc_para", p))

                for table in doc.tables:

                    for row in table.rows:

                        for cell in row.cells:

                            for p in cell.paragraphs:

                                if p.text.strip():

                                    text_elements.append(("doc_cell", p))

            elif ext == "xlsx":

                wb = load_workbook(BytesIO(file_bytes))

                for ws in wb.worksheets:

                    for row in ws.iter_rows():

                        for cell in row:

                            if isinstance(cell.value, str) and cell.value.strip():

                                text_elements.append(("xls_cell", cell))

            elif ext == "pptx":

                prs = Presentation(BytesIO(file_bytes))

                for slide in prs.slides:

                    for shape in slide.shapes:

                        if shape.has_text_frame:

                            for p in shape.text_frame.paragraphs:

                                if p.text.strip():

                                    text_elements.append(("ppt_para", p))

            total = len(text_elements)

            if total == 0:

                st.info("No text found in file.")

            else:

                progress_bar = st.progress(0)

                status_text = st.empty()

                for i, element in enumerate(text_elements):

                    elem_type, obj = element

                    translated = translate_text(obj.text, direction)

                    if elem_type == "doc_para" or elem_type == "doc_cell":

                        obj.text = translated

                    elif elem_type == "xls_cell":

                        obj.value = translated

                    elif elem_type == "ppt_para":

                        obj.text = translated

                    progress = (i + 1) / total

                    progress_bar.progress(progress)

                    status_text.text(f"Translating... {i + 1}/{total} elements")

                # Save the translated file

                if ext == "docx":

                    doc.save(output)

                elif ext == "xlsx":

                    wb.save(output)

                elif ext == "pptx":

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

# Teach new term

with st.expander("Teach Johny a new term (saved forever)"):

    c1, c2 = st.columns(2)

    with c1: eng = st.text_input("English")

    with c2: lao = st.text_input("Lao")

    if st.button("Save"):

        if eng.strip() and lao.strip():

            c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))

            conn.commit()

            st.success("Johny learned it!")

            st.rerun()

# Stats

c.execute("SELECT COUNT(*) FROM glossary")

count = c.fetchone()[0]

st.caption(f"Active glossary: {count} terms • Pure Gemini quality")

 
