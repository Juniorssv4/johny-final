import streamlit as st
import time
import openai
import google.generativeai as genai
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Grok + Gemini Hybrid • Unlimited + Fluent")

# API SETUP WITH YOUR KEYS
try:
    # Grok for routing (unlimited)
    grok_client = openai.OpenAI(
        api_key=st.secrets["GROK_API_KEY"],
        base_url="https://api.x.ai/v1"
    )
    grok_model = "grok-4-1-fast-non-reasoning"
    
    # Gemini for translation
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel('gemini-2.0-flash')
    
    st.success("✅ APIs connected!")
    
except Exception as e:
    st.error(f"❌ API connection failed: {str(e)}")
    st.stop()

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
        
        # GROK PRE-PROCESSING
        grok_prompt = f"""You are a routing assistant. Review this text for Mine Action terms and prepare it for Gemini translation. Ensure glossary terms are preserved. Return ONLY the pre-processed text ready for Gemini.

Text: {text}

Glossary: {glossary}"""
        
        grok_response = grok_client.chat.completions.create(
            model=grok_model,
            messages=[{"role": "user", "content": grok_prompt}],
            temperature=0.1
        )
        preprocessed_text = grok_response.choices[0].message.content.strip()
        
        # GEMINI TRANSLATION
        gemini_prompt = f"""You are an expert Mine Action translator for Laos.
Use EXACTLY these terms (never change them):
{glossary}

Translate the following pre-processed text to {target}.
Make it fluent, natural, idiomatic — like a native speaker.
Return ONLY the translated text, nothing else.

Pre-processed Text: {preprocessed_text}"""

        for attempt in range(3):
            try:
                response = gemini_model.generate_content(gemini_prompt)
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    time.sleep(40)
                else:
                    time.sleep(5)
        
        return "[Translation failed - try again]"
        
    except Exception as e:
        return f"[Error: {str(e)}]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

tab1, tab2 = st.tabs(["📁 Translate File", "📝 Translate Text"])

# TEXT TRANSLATION
with tab2:
    text = st.text_area("Enter text to translate", height=150, 
                       placeholder="Example: dogs stepped on mines")
    
   
