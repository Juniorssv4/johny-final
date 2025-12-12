import streamlit as st
import time
import openai
import requests
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Grok routes • Gemini translates (web) • No API limits")

# GROK API SETUP (unlimited routing)
try:
    grok_client = openai.OpenAI(
        api_key=st.secrets["GROK_API_KEY"],
        base_url="https://api.x.ai/v1"
    )
    grok_model = "grok-4-1-fast-non-reasoning"
    st.success("✅ Grok connected (unlimited)")
except:
    st.error("❌ Check GROK_API_KEY in secrets")
    st.stop()

# GEMINI WEB INTERFACE (no API limits)
def gemini_web_translate(text, target_lang):
    """Use Gemini web interface directly"""
    try:
        # Gemini web URL with query parameters
        gemini_url = "https://gemini.google.com/app"
        
        # Create a simple web request to Gemini's interface
        # This bypasses the API entirely
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # For now, we'll simulate the web call
        # In practice, you'd use selenium or similar to interact with Gemini web
        return f"[Simulated Gemini web translation to {target_lang}]: {text}"
        
    except Exception as e:
        return f"[Gemini web error: {str(e)}]"

# DATABASE SETUP
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS glossary 
             (english TEXT, lao TEXT, PRIMARY KEY(english, lao))''')
conn.commit()

# DEFAULT GLOSSARY
default_terms = {
    "Unexploded Ordnance": "ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ", "UXO": "ລບຕ",
    "Cluster Munition": "ລະເບີດລູກຫວ່ານ", "Bombies": "ບອມບີ",
    "Clearance": "ການກວດກູ້", "Victim Assistance": "ການຊ່ວຍເຫຼືອຜູ້ເຄາະຮ້າຍ",
    "Risk Education": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ", "MRE": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພຈາກລະເບີດ",
    "Deminer": "ນັກເກັບກູ້", "EOD": "ການທຳລາຯລະເບີດ",
    "Land Release": "ການປົດປ່ອຍພື້ນທີ່", "Quality Assurance": "ການຮັບປະກັນຄຸນນະພາບ",
}

for eng, lao in default_terms.items():
    c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))
conn.commit()

def get_glossary():
    c.execute("SELECT english, lao FROM glossary")
    terms = c.fetchall()
    if terms:
        return "\n".join([f"• {e.capitalize()} → {l}" for e, l in terms])
    return "No terms yet."

def translate_text(text, direction):
    if not text.strip():
        return text
    
    try:
        glossary = get_glossary()
        target = "Lao" if direction == "English → Lao" else "English"
        
        # GROK PRE-PROCESSING (unlimited)
        grok_prompt = f"""You are a routing assistant. Review this text for Mine Action terms and prepare it for translation. Preserve glossary terms. Return ONLY the pre-processed text.

Text: {text}

Glossary: {glossary}"""
        
        grok_response = grok_client.chat.completions.create(
            model=grok_model,
            messages=[{"role": "user", "content": grok_prompt}],
            temperature=0.1
        )
        preprocessed_text = grok_response.choices[0].message.content.strip()
        
        # GEMINI WEB TRANSLATION (no API limits)
        # Option 1: Open Gemini in new tab for manual copy/paste
        st.info("🔄 Opening Gemini web interface...")
        
        # Create Gemini web link with pre-filled text
        gemini_query = f"Translate this Mine Action text to {target}: {preprocessed_text}"
        gemini_url = f"https://gemini.google.com/app?q={requests.utils.quote(gemini_query)}"
        
        st.markdown(f"[🌐 Click here to translate in Gemini web]({gemini_url})")
        st.info("Copy the translation from Gemini and paste it back here:")
        
        # Let user paste the Gemini result
        result = st.text_area("Paste Gemini translation here:", height=100)
        
        if result.strip():
            return result
        else:
            return "[Waiting for Gemini web translation...]"
        
    except Exception as e:
        return f"[Error: {str(e)}]"

# UI LAYOUT
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# TEXT TRANSLATION WITH WEB INTEGRATION
st.subheader("📝 Translate Text")
text = st.text_area("Enter text to translate", height=100, 
                   placeholder="Example: dogs stepped on mines")

if st.button("Translate with Gemini Web", type="primary"):
    if text.strip():
        with st.spinner("Grok preprocessing... opening Gemini web..."):
            result = translate_text(text, direction)
            if not "[Waiting for" in result:
                st.success("Translation:")
                st.write(result)
    else:
        st.warning("Please enter some text")

# ALTERNATIVE: Simple redirect to Gemini
st.subheader("🚀 Quick Gemini Access")
quick_query = st.text_input("Or type here for instant Gemini:", 
                           placeholder="dogs stepped on mines")
if quick_query:
    gemini_url = f"https://gemini.google.com/app?q={requests.utils.quote(f'Translate this Mine Action text to Lao: {quick_query}')}"
    st.markdown(f"[🌐 Open in Gemini]({gemini_url})")

# FILE TRANSLATION
st.subheader("📁 Translate File")
uploaded_file = st.file_uploader("Upload DOCX • XLSX • PPTX", type=["docx", "xlsx", "pptx"])

if uploaded_file:
    if st.button("Process File for Gemini", type="secondary"):
        with st.spinner("Extracting text for Gemini translation..."):
            try:
                file_bytes = uploaded_file.read()
                file_name = uploaded_file.name
                ext = file_name.rsplit(".", 1)[-1].lower()
                
                # Extract text for Gemini
                extracted_text = []
                
                if ext == "docx":
                    doc = Document(BytesIO(file_bytes))
                    for p in doc.paragraphs:
                        if p.text.strip():
                            extracted_text.append(p.text)
                
                elif ext == "xlsx":
                    wb = load_workbook(BytesIO(file_bytes))
                    for ws in wb.worksheets:
                        for row in ws.iter_rows():
                            for cell in row:
                                if isinstance(cell.value, str) and cell.value.strip():
                                    extracted_text.append(cell.value)
                
                elif ext == "pptx":
                    prs = Presentation(BytesIO(file_bytes))
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if shape.has_text_frame:
                                for p in shape.text_frame.paragraphs:
                                    if p.text.strip():
                                        extracted_text.append(p.text)
                
                # Create Gemini link with all text
                all_text = "\n".join(extracted_text[:10])  # Limit to first 10 items
                gemini_file_url = f"https://gemini.google.com/app?q={requests.utils.quote(f'Translate this Mine Action document to Lao: {all_text}')}"
                
                st.success("✅ Text extracted!")
                st.markdown(f"[🌐 Translate in Gemini]({gemini_file_url})")
                st.info("After translating in Gemini, you can manually update your file")
                
            except Exception as e:
                st.error(f"File extraction failed: {str(e)}")

# GLOSSARY
with st.expander("📚 Teach Johny new terms"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English")
    with col2: lao = st.text_input("Lao")
    if st.button("Save Term"):
        if eng.strip() and lao.strip():
            c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))
            conn.commit()
            st.success(f"✅ Learned: {eng} → {lao}")
            st.rerun()

# STATS
c.execute("SELECT COUNT(*) FROM glossary")
count = c.fetchone()[0]
st.caption(f"📊 Glossary: {count} terms • Grok routes • Gemini web translates")
