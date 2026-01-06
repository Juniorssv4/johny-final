import streamlit as st
import time
import google.generativeai as genai
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

# GEMINI CONFIG
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Add GEMINI_API_KEY in Secrets")
    st.stop()

# Primary and fallback models
PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-1.5-flash"

if "current_model" not in st.session_state:
    st.session_state.current_model = PRIMARY_MODEL

model = genai.GenerativeModel(st.session_state.current_model)

# Backoff
@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def safe_generate_content(prompt):
    return model.generate_content(prompt)

# Persistent Glossary — saved forever in repo file
GLOSSARY_FILE = "glossary.txt"

if "glossary" not in st.session_state:
    try:
        with open(GLOSSARY_FILE, "r") as f:
            lines = f.readlines()
        glossary_dict = {}
        for line in lines:
            if ":" in line:
                eng, lao = line.strip().split(":", 1)
                glossary_dict[eng.strip().lower()] = lao.strip()
        st.session_state.glossary = glossary_dict
    except FileNotFoundError:
        st.session_state.glossary = {}

glossary = st.session_state.glossary

def save_glossary():
    with open(GLOSSARY_FILE, "w") as f:
        for eng, lao in glossary.items():
            f.write(f"{eng}:{lao}\n")

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
    except RetryError as e:
        if "429" in str(e.last_attempt.exception()) or "quota" in str(e.last_attempt.exception()).lower():
            if st.session_state.current_model == PRIMARY_MODEL:
                st.session_state.current_model = FALLBACK_MODEL
                st.info("Rate limit on gemini-2.5-flash — switched to gemini-1.5-flash.")
                global model
                model = genai.GenerativeModel(FALLBACK_MODEL)
                response = model.generate_content(prompt)
                return response.text.strip()
        st.error("Timed out after retries — try again in 5 minutes.")
        return "[Failed — try later]"
    except Exception as e:
        st.error(f"API error: {str(e)}")
        return "[Failed — try again]"

# UI
st.set_page_config(
    page_title="Johny",
    page_icon="https://raw.githubusercontent.com/Juniorssv4/johny-final/main/Johny.png",
    layout="centered"
)
st.title("😊 Johny — NPA Lao Translator")

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
                file_name = uploaded_file.name
                ext = file_name.rsplit(".", 1)[-1].lower()
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
                st.success("File translated perfectly!")

                st.download_button(
                    label="📥 Download Translated File",
                    data=output,
                    file_name=f"TRANSLATED_{file_name}",
                    mime="application/octet-stream",
                    type="primary",
                    use_container_width=True
                )

# Teach term
with st.expander("➕ Teach Johny a new term (saved forever)"):
    c1, c2 = st.columns(2)
    with c1: eng = st.text_input("English")
    with c2: lao = st.text_input("Lao")
    if st.button("Save"):
        if eng.strip() and lao.strip():
            glossary[eng.strip().lower()] = lao.strip()
            save_glossary()
            st.success("Saved forever!")
            st.rerun()

st.caption(f"Active glossary: {len(glossary)} terms • Model: {st.session_state.current_model}")
