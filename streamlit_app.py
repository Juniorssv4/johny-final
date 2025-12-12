import streamlit as st

import openai

import google.generativeai as genai

import sqlite3

from io import BytesIO

from docx import Document

from openpyxl import load_workbook

from pptx import Presentation

# GROK ROUTES (UNLIMITED) + GEMINI TRANSLATES (FLUENT LAO)

try:

    # Grok for routing/tool-calling

    grok_client = openai.OpenAI(

        api_key=st.secrets["GROK_API_KEY"],

        base_url="https://api.x.ai/v1"

    )

    grok_model = "grok-4-1-fast-non-reasoning"

    # Gemini for translation

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    gemini_model = genai.GenerativeModel('gemini-2.5-flash')

except:

    st.error("API keys missing — add GROK_API_KEY and GEMINI_API_KEY in Secrets")

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

    "Deminer": "ນັກເກັບກູ້", "EOD": "ການທຳລາຯລະເບີດ",

    "Land Release": "ການປົດປ່ອຍພື້ນທີ່", "Quality Assurance": "ການຮັບປະກັນຄຸນນະພາບ",

    "Confirmed Hazardous Area": "ພື້ນທີ່ຢັ້ງຢືນວ່າເປັນອັນຕະລາຯ", "CHA": "ພື້ນທີ່ຢັ້ງຢືນວ່າເປັນອັນຕະລາຯ",

    "Suspected Hazardous Area": "ພື້ນທີ່ສົງໃສວ່າເປັນອັນຕະລາຯ", "SHA": "ພື້ນທີ່ສົງໃສວ່າເປັນອັນຕະລາຯ",

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

    # Grok routes/pre-processes (unlimited)

    grok_prompt = f"""You are a routing assistant. Review this text for Mine Action terms and prepare it for Gemini translation. Ensure glossary terms are preserved. Return ONLY the pre-processed text ready for Gemini.

Text: {text}

Glossary: {glossary}"""

    try:

        grok_response = grok_client.chat.completions.create(

            model=grok_model,

            messages=[{"role": "user", "content": grok_prompt}],

            temperature=0.1

        )

        preprocessed_text = grok_response.choices[0].message.content.strip()

    except:

        preprocessed_text = text  # Fallback

    # Gemini translates (fluent Lao)

    gemini_prompt = f"""You are an expert Mine Action translator for Laos.

Use EXACTLY these terms (never change them):

{glossary}

Translate the following pre-processed text to {target}.

Make it fluent, natural, idiomatic — like a native speaker.

Return ONLY the translated text, nothing else.

Pre-processed Text: {preprocessed_text}"""

    for attempt in range(3):  # Retry on 429

        try:

            response = gemini_model.generate_content(gemini_prompt)

            return response.text.strip()

        except Exception as e:

            if "429" in str(e):

                time.sleep(40)

            else:

                time.sleep(5)

    return "[Translation failed — try again]"

# UI

st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")

st.title("Johny — NPA Lao Translator")

st.caption("Grok + Gemini Hybrid • Unlimited + Fluent • Add to Home screen = real app")

direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["Translate File", "Translate Text"])

# FILE TRANSLATION — GROK ROUTES, GEMINI TRANSLATES

with tab1:

    uploaded_file = st.file_uploader("Upload DOCX • XLSX • PPTX", type=["docx", "xlsx", "pptx"])

    if uploaded_file and st.button("Translate File", type="primary"):

        with st.spinner("Grok routing + Gemini translating..."):

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

        with st.spinner("Grok + Gemini translating..."):

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

st.caption(f"Active glossary: {count} terms • Grok + Gemini Hybrid")

st.balloons()
 
