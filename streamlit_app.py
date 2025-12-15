import streamlit as st
import time
import google.generativeai as genai
# NEW IMPORT: Import the specific error class for 429/quota errors
from google.generativeai.errors import APIError 
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
# UPDATED IMPORT: Added 'retry_if_exception_type' for better control
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError 

# GEMINI — PERFECT LAO + EXPONENTIAL BACKOFF RETRY
try:
    # Use the new, correct client import name
    from google import genai as new_genai 
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
except:
    st.error("Add your Gemini key in Secrets → GEMINI_API_KEY")
    st.stop()

# Exponential backoff decorator — retries ONLY on APIError (including 429)
@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    # THIS IS THE CRITICAL FIX: Only retry when a known API error occurs
    retry=retry_if_exception_type(APIError) 
)
def safe_generate_content(prompt):
    """Safe API call with backoff for rate limits."""
    return model.generate_content(prompt)

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

    try:
        response = safe_generate_content(prompt)
        return response.text.strip()
    except RetryError:
        # This executes only if all 6 attempts failed, which means the rate limit is severe
        st.error("Translation timed out after retries (6 attempts, 1 min max wait). The rate limit is too high. Try again in 5 minutes.")
        return "[Translation failed — Quota exhausted, please wait]"
    except Exception as e:
        # Catch any other unexpected API errors
        st.error(f"General API error: {str(e)}")
        return "[Translation failed — Check API Key or Model]"

# UI
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate File", "Translate Text"])

with tab1:
    uploaded_file = st.file_uploader(
        "Upload DOCX • XLSX • PPTX (max 10MB)",
        type=["docx", "xlsx", "pptx"]
    )

    if uploaded_file is not None:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File too large! Maximum size is 10MB.")
            st.stop()

    if uploaded_file and st.button("Translate File", type="primary"):
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        ext = file_name.rsplit(".", 1)[-1].lower()

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

        progress_bar = st.progress(0)
        status_text = st.empty()

        output = BytesIO()

        translated_count = 0
        # Placeholder for the new file object
        translated_file_object = None 

        for element_type, element in elements_list:
            status_text.text(f"Translating... {translated_count}/{total_elements} ({int((translated_count/total_elements)*100)}%)")

            if element_type in ["doc_para", "doc_cell"]:
                translated = translate_text(element.text, direction)
                element.text = translated
                translated_file_object = doc
            elif element_type == "xls":
                translated = translate_text(element.value, direction)
                element.value = translated
                translated_file_object = wb
            elif element_type == "ppt":
                translated = translate_text(element.text, direction)
                element.text = translated
                translated_file_object = prs

            translated_count += 1
            progress_bar.progress(translated_count / total_elements)

        status_text.text(f"Translation complete! {total_elements}/{total_elements} (100%)")
        progress_bar.progress(1.0)

        # Save the translated file
        if translated_file_object:
            if ext == "docx":
                translated_file_object.save(output)
            elif ext == "xlsx":
                translated_file_object.save(output)
            elif ext == "pptx":
                translated_file_object.save(output)
            
            output.seek(0)
            st.success("File translated perfectly!")
            st.download_button("Download Translated File", output, f"TRANSLATED_{file_name}")
        else:
            st.error("Error: Could not save the translated file.")

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
st.caption(f"Active glossary: {count} terms")
