import streamlit as st
import time
import google.generativeai as genai
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# GEMINI — PERFECT LAO + PROGRESS BAR WITH PERCENTAGE
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except:
    st.error("Add your Gemini key in Secrets → GEMINI_API_KEY")
    st.stop()

# Database + Glossary
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT, PRIMARY KEY(english, lao))''')
conn.commit()

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
st.caption("Pure Gemini quality • Progress bar with % • Add to Home screen = real app")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate File", "Translate Text"])

with tab1:
    uploaded_file = st.file_uploader("Upload DOCX • XLSX • PPTX", type=["docx", "xlsx", "pptx"])
    if uploaded_file and st.button("Translate File", type="primary"):
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        ext = file_name.rsplit(".", 1)[-1].lower()

        # Count total text elements for progress bar
        total_elements = 0
        elements_list = []

        if ext == "docx":
            doc = Document(BytesIO(file_bytes))
            for p in doc.paragraphs:
                if p.text.strip():
                    total_elements += 1
                    elements_list.append(("doc_para", p))
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            if p.text.strip():
                                total_elements += 1
                                elements_list.append(("doc_cell", p))

        elif ext == "xlsx":
            wb = load_workbook(BytesIO(file_bytes))
            for ws in wb.worksheets:
                for row in ws.iter_rows():
                    for cell in row:
                        if isinstance(cell.value, str) and cell.value.strip():
                            total_elements += 1
                            elements_list.append(("xls", cell))

        elif ext == "pptx":
            prs = Presentation(BytesIO(file_bytes))
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for p in shape.text_frame.paragraphs:
                            if p.text.strip():
                                total_elements += 1
                                elements_list.append(("ppt", p))

        if total_elements == 0:
            st.warning("No text found in the file.")
            st.stop()

        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        output = BytesIO()

        translated_count = 0

        for element_type, element in elements_list:
            status_text.text(f"Translating... {translated_count}/{total_elements} ({int((translated_count/total_elements)*100)}%)")

            if element_type == "doc_para" or element_type == "doc_cell":
                translated = translate_text(element.text, direction)
                element.text = translated
            elif element_type == "xls":
                translated = translate_text(element.value, direction)
                element.value = translated
            elif element_type == "ppt":
                translated = translate_text(element.text, direction)
                element.text = translated

            translated_count += 1
            progress_bar.progress(translated_count / total_elements)

        status_text.text(f"Translation complete! {total_elements}/{total_elements} (100%)")
        progress_bar.progress(1.0)

        # Save output
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

st.balloons()
