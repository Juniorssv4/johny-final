import streamlit as st
import time
import google.generativeai as genai
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# GEMINI — PERFECT LAO + SMART RETRY (NO 429 EVER)
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
    prompt = f"""Expert Mine Action translator for Laos.
Use EXACTLY these terms (never change them):
{glossary}

Translate to {target} in fluent, natural, idiomatic style (native-speaker phrasing).
Return ONLY the translated text.

Text: {text}"""

    for i in range(6):  # max 6 retries
        try:
            r = model.generate_content(prompt)
            return r.text.strip()
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 40 + i * 10
                st.toast(f"Rate limit — waiting {wait}s...")
                time.sleep(wait)
            else:
                return f"[Error: {e}]"
    return "[Translation timed out]"

# UI
st.set_page_config(page_title="Johny", page_icon="Flag of Laos", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Gemini quality • Smart retry • Add to Home screen = real app")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate File", "Translate Text"])

with tab1:
    uploaded = st.file_uploader("Upload DOCX/XLSX/PPTX", type=["docx","xlsx","pptx"])
    if uploaded and st.button("Translate File", type="primary"):
        with st.spinner("Translating file..."):
            bytes_data = uploaded.read()
            ext = uploaded.name.rsplit(".",1)[-1].lower()
            out = BytesIO()

            if ext == "docx":
                doc = Document(BytesIO(bytes_data))
                for p in doc.paragraphs:
                    if p.text.strip():
                        p.text = translate_text(p.text, direction)
                for t in doc.tables:
                    for r in t.rows:
                        for cell in r.cells:
                            for p in cell.paragraphs:
                                if p.text.strip():
                                    p.text = translate_text(p.text, direction)
                doc.save(out)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(bytes_data))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value,str) and cell.value.strip():
                                cell.value = translate_text(cell.value, direction)
                wb.save(out)

            elif ext == "pptx":
                prs = Presentation(BytesIO(bytes_data))
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for p in shape.text_frame.paragraphs:
                                if p.text.strip():
                                    p.text = translate_text(p.text, direction)
                prs.save(out)

            out.seek(0)
            st.success("File translated!")
            st.download_button("Download Translated File", out, f"translated_{uploaded.name}")

with tab2:
    txt = st.text_area("Enter text", height=150)
    if st.button("Translate Text"):
        with st.spinner("Translating..."):
            st.write(translate_text(txt, direction))

with st.expander("Teach Johny a new term"):
    c1,c2 = st.columns(2)
    with c1: e = st.text_input("English")
    with c2: l = st.text_input("Lao")
    if st.button("Save"):
        if e and l:
            c.execute("INSERT OR IGNORE INTO glossary VALUES (?,?)", (e.lower(), l))
            conn.commit()
            st.success("Learned!")
            st.rerun()

c.execute("SELECT COUNT(*) FROM glossary")
st.caption(f"Glossary: {c.fetchone()[0]} terms • Pure Gemini quality")

st.balloons()
