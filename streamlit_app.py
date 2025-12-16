import streamlit as st
import time
import google.generativeai as genai
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

# GEMINI CONFIG
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])  # Fixed key name
    model = genai.GenerativeModel("gemini-2.5-flash")
except:
    st.error("Add GEMINI_API_KEY in Secrets")
    st.stop()

# Backoff for rate limits
@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def safe_generate_content(prompt):
    return model.generate_content(prompt)

# Persistent Glossary (saved forever in DB)
conn = sqlite3.connect("glossary.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS glossary (english TEXT PRIMARY KEY, lao TEXT)''')
conn.commit()

def load_glossary():
    c.execute("SELECT english, lao FROM glossary")
    return dict(c.fetchall())

def save_term(english, lao):
    c.execute("INSERT OR REPLACE INTO glossary VALUES (?, ?)", (english.lower(), lao))
    conn.commit()

glossary = load_glossary()

def get_glossary_prompt():
    if glossary:
        terms = "\n".join([f"• {e.capitalize()} → {l}" for e, l in glossary.items()])
        return f"Use EXACTLY these terms:\n{terms}\n"
    return ""

def translate_text(text, direction):
    if not text.strip():
        return text
    target = "Lao" if direction == "English → Lao" else "English"
    prompt = f"""{get_glossary_prompt()}Translate ONLY the text to {target}.
Return ONLY the translation.

Text: {text}"""

    try:
        response = safe_generate_content(prompt)
        return response.text.strip()
    except RetryError:
        st.error("Timed out after retries — rate limit delay. Try again in 5 minutes.")
        return "[Failed — try later]"
    except Exception as e:
        st.error(f"API error: {str(e)}")
        return "[Failed — try again]"

# UI
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate Text", "Translate File"])

with tab1:
    text = st.text_area("Enter text to translate", height=200)
    if st.button("Translate Text", type="primary"):
        with st.spinner("Translating..."):
            result = translate_text(text, direction)
            st.success("Translation:")
            st.write(result)

with tab2:
    uploaded_file = st.file_uploader("Upload DOCX • XLSX • PPTX (max 10MB)", type=["docx", "xlsx", "pptx"])

    if uploaded_file:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File too large! Max 10MB.")
            st.stop()

        if st.button("Translate File", type="primary"):
            with st.spinner("Translating file..."):
                file_bytes = uploaded_file.read()
                ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
                output = BytesIO()

                total_elements = 0
                elements_list = []

                if ext == "docx":
                    doc = Document(BytesIO(file_bytes))
                    for p in doc.paragraphs:
                        if p.text.strip():
                            total_elements += 1
                            elements_list.append(("para", p))
                    for table in doc.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                for p in cell.paragraphs:
                                    if p.text.strip():
                                        total_elements += 1
                                        elements_list.append(("para", p))

                elif ext == "xlsx":
                    wb = load_workbook(BytesIO(file_bytes))
                    for ws in wb.worksheets:
                        for row in ws.iter_rows():
                            for cell in row:
                                if isinstance(cell.value, str) and cell.value.strip():
                                    total_elements += 1
                                    elements_list.append(("cell", cell))

                elif ext == "pptx":
                    prs = Presentation(BytesIO(file_bytes))
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if shape.has_text_frame:
                                for p in shape.text_frame.paragraphs:
                                    if p.text.strip():
                                        total_elements += 1
                                        elements_list.append(("para", p))

                if total_elements == 0:
                    st.warning("No text found.")
                    st.stop()

                progress_bar = st.progress(0)
                status_text = st.empty()

                translated_count = 0

                for element_type, element in elements_list:
                    status_text.text(f"Translating... {translated_count}/{total_elements}")

                    if element_type == "para":
                        translated = translate_text(element.text, direction)
                        element.text = translated
                    elif element_type == "cell":
                        translated = translate_text(element.value, direction)
                        element.value = translated

                    translated_count += 1
                    progress_bar.progress(translated_count / total_elements)

                status_text.text("Saving file...")
                if ext == "docx":
                    doc.save(output)
                elif ext == "xlsx":
                    wb.save(output)
                elif ext == "pptx":
                    prs.save(output)

                output.seek(0)
                st.success("File translated!")
                st.download_button("Download Translated File", output, f"TRANSLATED_{uploaded_file.name}")

# Teach term
with st.expander("➕ Teach Johny a new term (saved forever)"):
    c1, c2 = st.columns(2)
    with c1: eng = st.text_input("English")
    with c2: lao = st.text_input("Lao")
    if st.button("Save"):
        if eng.strip() and lao.strip():
            save_term(eng.strip(), lao.strip())
            st.success("Saved!")
            st.rerun()

st.caption(f"Active glossary: {len(glossary)} terms")
