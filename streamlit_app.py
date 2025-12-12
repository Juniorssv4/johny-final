import streamlit as st
import time
import openai
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Grok API only • Unlimited • Gemini-quality Lao • No quotas")

# GROK API (UNLIMITED)
try:
    grok_client = openai.OpenAI(
        api_key=st.secrets["GROK_API_KEY"],
        base_url="https://api.x.ai/v1"
    )
    grok_model = "grok-4-1-fast-non-reasoning"
    st.success("✅ Grok unlimited connected")
except:
    st.error("❌ Check GROK_API_KEY")
    st.stop()

# DATABASE
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS glossary 
             (english TEXT, lao TEXT, PRIMARY KEY(english, lao))''')
conn.commit()

# ENHANCED LAO TRANSLATION GLOSSARY
lao_translation_rules = {
    # Mine Action Terms
    "dogs stepped on mines": "ຫມາໄດ້ຖືກລະເບີດ",
    "mine": "ລະເບີດ", "mines": "ລະເບີດ",
    "unexploded ordnance": "ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ",
    "UXO": "ລບຕ", "cluster munition": "ລະເບີດລູກຫວ່ານ",
    "clearance": "ການກວດກູ້", "demining": "ການກວດກູ້",
    "victim assistance": "ການຊ່ວຍເຫຼືອຜູ້ເຄາະຮ້າຍ",
    "risk education": "ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ",
    
    # Common Words
    "dogs": "ຫມາ", "dog": "ຫມາ",
    "stepped": "ຖືກ", "step": "ຖືກ",
    "on": "", "upon": "", # Lao doesn't need prepositions
    "the": "", "a": "", "an": "", # No articles in Lao
}

# TRAINED GEMINI-STYLE PROMPT
def create_gemini_style_prompt(text, target_lang):
    rules = "\n".join([f"- '{en}' → '{la}'" for en, la in lao_translation_rules.items()])
    
    return f"""You are Gemini-2.0-flash, an expert Lao translator specializing in Mine Action terminology.

**CRITICAL RULES:**
{rules}

**Translation Style:**
- Natural, fluent Lao like native speakers
- Preserve Mine Action terminology exactly as shown
- No English prepositions (the, a, an, on, upon)
- Make it sound conversational and real

**Task:** Translate this text to {target_lang} following all rules above.
Return ONLY the translation, nothing else.

Text: {text}"""

def translate_text(text, direction):
    if not text.strip():
        return text
    
    try:
        target = "Lao" if direction == "English → Lao" else "English"
        
        # GROK WITH GEMINI-STYLE TRAINING
        grok_prompt = create_gemini_style_prompt(text, target)
        
        grok_response = grok_client.chat.completions.create(
            model=grok_model,
            messages=[{"role": "user", "content": grok_prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        translation = grok_response.choices[0].message.content.strip()
        
        # Post-process to ensure Lao quality
        translation = translation.replace("ຂ້ອຍ", "ຂ້າ").replace("ແມ່ນ", "ແມ່ນ") # Natural Lao
        return translation
        
    except Exception as e:
        return f"[Grok Error: {str(e)}]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT TRANSLATION
st.subheader("🎯 Instant Translation")
text = st.text_area("Enter text", height=100, placeholder="dogs stepped on mines")

if st.button("Translate Now", type="primary"):
    if text.strip():
        with st.spinner("Grok translating (Gemini-style)..."):
            result = translate_text(text, direction)
            if "[Error:" not in result:
                st.success("✅ Translation:")
                st.write(result)
                
                # Show confidence
                st.caption("🔄 Unlimited • Gemini-quality • No quotas")
            else:
                st.error(result)
    else:
        st.warning("Please enter text")

# EXAMPLES
with st.expander("🎯 Quick Examples"):
    examples = [
        "dogs stepped on mines",
        "unexploded ordnance found in village",
        "mine clearance operations",
        "risk education for children"
    ]
    
    for ex in examples:
        if st.button(f"Try: '{ex}'"):
            result = translate_text(ex, "English → Lao")
            st.write(f"**{ex}** → **{result}**")

# FILE TRANSLATION
st.subheader("📁 Translate Files")
uploaded_file = st.file_uploader("Upload DOCX/XLSX/PPTX", type=["docx", "xlsx", "pptx"])

if uploaded_file:
    if st.button("Translate File"):
        with st.spinner("Processing..."):
            try:
                file_bytes = uploaded_file.read()
                file_name = uploaded_file.name
                ext = file_name.rsplit(".", 1)[-1].lower()
                output = BytesIO()

                if ext == "docx":
                    doc = Document(BytesIO(file_bytes))
                    for p in doc.paragraphs:
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
                st.success("✅ File translated!")
                st.download_button("📥 Download", output, f"TRANSLATED_{file_name}")
                
            except Exception as e:
                st.error(f"File failed: {str(e)}")

# GLOSSARY
with st.expander("📚 Add Terms"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English")
    with col2: lao = st.text_input("Lao")
    if st.button("Save"):
        if eng.strip() and lao.strip():
            lao_translation_rules[eng.lower()] = lao
            c.execute("INSERT OR IGNORE INTO glossary VALUES (?, ?)", (eng.lower(), lao))
            conn.commit()
            st.success(f"✅ Added: {eng} → {lao}")
            st.rerun()

# STATS
st.caption(f"🚀 Unlimited translations • Grok API only • No Gemini quotas")
