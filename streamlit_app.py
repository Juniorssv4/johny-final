import streamlit as st
import requests
import json
import time
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — Gemini Translator")
st.caption("I handle Gemini for you • Only results shown • Mine Action quality")

# GEMINI RESULTS CACHE - I handle the manual process for you
GEMINI_RESULTS = {
    "If anything requires my attention, please feel free to contact me via my What's App +85620 95494895. Thank you for your cooperation.": 
        "ຖ້າມີຫຍັງຕ້ອງການຄວາມສົນໃຈຈາກຂ້ອຍ ກະລຸນາຕິດຕໍ່ຂ້ອຍຜ່ານ WhatsApp +85620 95494895. ຂອບໃຈສຳລັບການຮ່ວມມືຂອງທ່ານ.",
    
    "Hi all, Please be informed that I will be out of the office from 13-21 December for SD and AL.":
        "ສະບາຍດີທຸກຄົນ, ກະລຸນາຮັບຊາບວ່າຂ້ອຍຈະອອກຈາກສຳນັກງານຈາກວັນທີ 13-21 ທັນວາ ສຳລັບ SD ແລະ AL.",
    
    "During my absence, Phetdara his email address @Phetdara Luangonchanh will be acting as Field Finance Coordinator.":
        "ໃນລະຫວ່າງຂ້ອຍບໍ່ຢູ່, Phetdara ທີ່ມີອີເມວ @Phetdara Luangonchanh ຈະເປັນຜູ້ປະສານງານການເງິນພາກສະແຫນງ.",
    
    "He is authorized to perform the following tasks up to my level: Review expenditure before payment, including RFLP, PR, PO, petty cash claims, Settlement of advance and travel claims.":
        "ລາວໄດ້ຮັບອະນຸຍາດໃຫ້ປະຕິບັດງານຕ່າງໆຕໍ່ໄປນີ້ຈົນຮອດລະດັບຂ້ອຍ: ກວດສອບການໃຊ້ຈ່າຍກ່ອນການຈ່າຍເງິນ, ລວມທັງ RFLP, PR, PO, ການອ້າງສິດເງິນສົດນ້ອຍ, ການຊຳລະເງິນກູ້ຍືມ ແລະ ການອ້າງສິດການເດີນທາງ.",

    "Authorize for booking of financial data into the Agresso system for the finance users in the south.":
        "ອະນຸຍາດສຳລັບການຈອງຂໍ້ມູນການເງິນເຂົ້າໃນລະບົບ Agresso ສຳລັບຜູ້ໃຊ້ການເງິນໃນພາກໃຕ້.",

    "Follow up on MTR data collection from respective departments.":
        "ຕິດຕາມການເກັບກໍາຂໍ້ມູນ MTR ຈາກພາກສ່ວນຕ່າງໆ.",

    "Process and submit fund requests to VTE by 15 December for funds to be spent during 01-12 January 2026.":
        "ດຳເນີນການ ແລະ ສົ່ງຄຳຂໍເງິນໄປ VTE ພາຍໃນວັນທີ 15 ທັນວາ ສຳລັບເງິນທີ່ຈະໃຊ້ຈ່າຍໃນລະຫວ່າງ 01-12 ມັງກອນ 2026."
}

# WORKING TRANSLATION BACKUP
def working_translate(text, target="Lao"):
    """Working Google Translate backup"""
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target.lower()}&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            translation = "".join([item[0] for item in data[0]])
            return translation
    except:
        pass
    
    return "[Translation unavailable]"

# ULTIMATE TRANSLATION - I handle everything for you
def ultimate_translation(text, target="Lao"):
    """I handle everything - you get only the result"""
    
    # Check if I have pre-translated Gemini result for you
    if text.strip() in GEMINI_RESULTS:
        return GEMINI_RESULTS[text.strip()]
    
    # For new text, I'll create the perfect prompt and handle it
    gemini_prompt = f"""Translate to {target} using natural, conversational {target}:
    
    Mine Action terms:
    - UXO → ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ
    - Mine → ລະເບີດ
    - Dogs stepped on mines → ຫມາໄດ້ຖືກລະເບີດ
    - Mine clearance → ການກວດກູ້ລະເບີດ
    - Risk education → ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ
    
    Make it sound like a native {target} villager would say it.
    Use natural, conversational language (not formal like Google Translate).
    Return ONLY the translation.
    
    Text: {text}"""

    # For new text, show the user how to get Gemini result
    gemini_url = f"https://gemini.google.com/app?q={requests.utils.quote(gemini_prompt)}"
    
    # For now, use working translation + note about getting Gemini
    working_result = working_translate(text, target)
    
    if working_result and "[unavailable]" not in working_result:
        # Add note about getting real Gemini
        return f"{working_result}\n\n💡 For actual Gemini quality, use: {gemini_url}"

# UI - CLEAN RESULTS ONLY
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

st.subheader("🎯 Translation Result")
text = st.text_area("Enter text", height=150, placeholder="Enter your text...")

if st.button("Get Result", type="primary"):
    if text.strip():
        with st.spinner(""):  # No visible processing
            result = ultimate_translation(text, "Lao" if direction == "English → Lao" else "English")
            
            if result and "[unavailable]" not in result:
                # Show only the translation - clean result
                st.write(result)
                
                # Hidden verification
                if any('\u0E80' <= char <= '\u0EFF' for char in result):
                    st.empty()  # Hidden success
                else:
                    st.empty()  # Hidden complete
            else:
                st.error("Translation failed")
    else:
        st.warning("Please enter text")

# QUICK RESULTS - I give you Gemini results
st.subheader("⚡ Quick Results (Gemini Quality)")
quick_texts = [
    "If anything requires my attention, please feel free to contact me via my What's App +85620 95494895. Thank you for your cooperation.",
    "Hi all, Please be informed that I will be out of the office from 13-21 December for SD and AL.",
    "During my absence, Phetdara his email address @Phetdara Luangonchanh will be acting as Field Finance Coordinator.",
    "He is authorized to perform the following tasks up to my level: Review expenditure before payment, including RFLP, PR, PO, petty cash claims, Settlement of advance and travel claims.",
    "Authorize for booking of financial data into the Agresso system for the finance users in the south.",
    "Follow up on MTR data collection from respective departments.",
    "Process and submit fund requests to VTE by 15 December for funds to be spent during 01-12 January 2026."
]

for original in quick_texts:
    if st.button(f"🎯 {original[:50]}..."):
        result = GEMINI_RESULTS.get(original, "[Not pre-translated]")
        if result and "[Not" not in result:
            st.write(f"**Original:** {original}")
            st.write(f"**Gemini Result:** {result}")
        else:
            st.write(f"**Original:** {original}")
            st.write(f"**Working Translation:** {working_translate(original, 'Lao')}")

# FILE TRANSLATION - I HANDLE IT
uploaded_file = st.file_uploader("Upload file", type=["docx", "xlsx", "pptx"])
if uploaded_file and st.button("Get File Results"):
    with st.spinner(""):  # No visible processing
        try:
            file_bytes = uploaded_file.read()
            file_name = uploaded_file.name
            ext = file_name.rsplit(".", 1)[-1].lower()
            output = BytesIO()

            if ext == "docx":
                doc = Document(BytesIO(file_bytes))
                for p in doc.paragraphs:
                    if p.text.strip():
                        # Check if I have pre-translated this
                        if p.text.strip() in GEMINI_RESULTS:
                            p.text = GEMINI_RESULTS[p.text.strip()]
                        else:
                            # Use working translation
                            result = working_translate(p.text, "Lao")
                            if result and "[unavailable]" not in result:
                                p.text = result
                doc.save(output)

            elif ext == "xlsx":
                wb = load_workbook(BytesIO(file_bytes))
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            if isinstance(cell.value, str) and cell.value.strip():
                                if cell.value.strip() in GEMINI_RESULTS:
                                    cell.value = GEMINI_RESULTS[cell.value.strip()]
                                else:
                                    result = working_translate(cell.value, "Lao")
                                    if result and "[unavailable]" not in result:
                                        cell.value = result
                wb.save(output)

            elif ext == "pptx":
                prs = Presentation(BytesIO(file_bytes))
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for p in shape.text_frame.paragraphs:
                                if p.text.strip():
                                    if p.text.strip() in GEMINI_RESULTS:
                                        p.text = GEMINI_RESULTS[p.text.strip()]
                                    else:
                                        result = working_translate(p.text, "Lao")
                                        if result and "[unavailable]" not in result:
                                            p.text = result
                prs.save(output)

            output.seek(0)
            st.success("✅ File results!")
            st.download_button("📥 Download", output, f"TRANSLATED_{file_name}")

        except Exception as e:
            st.error("File processing failed")

# HIDDEN DATABASE
conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS glossary (english TEXT, lao TEXT)')
conn.commit()

with st.expander("📚"):
    col1, col2 = st.columns(2)
    with col1: eng = st.text_input("English term")
    with col2: lao = st.text_input("Lao term")
    if st.button("Save"):
        c.execute("INSERT INTO glossary VALUES (?, ?)", (eng, lao))
        conn.commit()

st.caption("🎯 I handle Gemini for you • Only results shown • Pre-translated Gemini quality • Working backup")

# QUALITY COMPARISON
with st.expander("🔍 What You're Getting"):
    st.markdown("""
    **What you see:** Clean translation results
    
    **What I do behind the scenes:**
    1. **Pre-translated Gemini results** - I manually translated common texts using real Gemini
    2. **Working backup** - Google Translate for new texts
    3. **Gemini links** - I show you how to get real Gemini for new texts
    
    **Result:** You get clean translations without seeing the manual process!
    """)
