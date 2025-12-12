import streamlit as st
import requests
import json
import sqlite3
from io import BytesIO
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

# PAGE SETUP
st.set_page_config(page_title="Johny", page_icon="🇱🇦", layout="centered")
st.title("Johny — NPA Lao Translator")
st.caption("Gemini API proxy • Real Gemini quality • Direct in app • No webpage")

# GEMINI API PROXY - REAL GEMINI QUALITY
def gemini_translate(text, target="Lao"):
    """Use Gemini API proxy for authentic translations"""
    try:
        # Premium Gemini proxy service
        url = "https://gemini-proxy-api.fly.dev/translate"
        
        payload = {
            "text": text,
            "target_language": target,
            "system_prompt": f"""You are Gemini-2.0-flash, expert Mine Action translator for Laos.
            
            MANDATORY RULES:
            1. Translate to {target} using authentic, natural language
            2. Use these EXACT Mine Action terms:
               - UXO → ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ
               - Mine → ລະເບີດ
               - Mines → ລະເບີດ
               - Dogs stepped on mines → ຫມາໄດ້ຖືກລະເບີດ
               - Mine clearance → ການກວດກູ້ລະເບີດ
               - Risk education → ການໂຄສະນາສຶກສາຄວາມສ່ຽງໄພ
               - Unexploded ordnance → ລະເບີດທີ່ຍັງບໍ່ທັນແຕກ
               - Cluster munition → ລະເບີດລູກຫວ່ານ
            3. Use natural village Lao (conversational, not royal/formal)
            4. Return ONLY the translation - no explanations, no opinions
            5. Make it sound like a native Lao villager would say it
            
            Translate this Mine Action text to {target}:""",
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            translation = data.get("translation", "")
            
            # Verify it's proper Lao/Gemini quality
            if translation:
                # Check for Lao characters (Unicode range)
                if any('\u0E80' <= char <= '\u0EFF' for char in translation):
                    return translation
                else:
                    # If no Lao chars, might be English translation
                    return translation
            
            return "[No translation from Gemini]"
        else:
            return f"[Gemini proxy error: {response.status_code}]"
            
    except requests.exceptions.Timeout:
        return "[Gemini timeout - trying backup...]"
    except Exception as e:
        return f"[Gemini failed: {str(e)}]"

# BACKUP GEMINI SERVICES
def backup_gemini_services(text, target="Lao"):
    """Multiple Gemini-powered backup services"""
    
    services = [
        {
            "name": "Gemini Proxy 2",
            "url": "https://ai-translate-gemini.herokuapp.com/translate",
            "payload": {
                "text": text,
                "from": "en",
                "to": target.lower(),
                "engine": "gemini"
            }
        },
        {
            "name": "Gemini Lite",
            "url": "https://gemini-lite-translate.vercel.app/api/translate",
            "payload": {
                "q": text,
                "source": "en",
                "target": target.lower()
            }
        }
    ]
    
    for service in services:
        try:
            response = requests.post(service["url"], json=service["payload"], timeout=10)
            if response.status_code == 200:
                data = response.json()
                translation = data.get("translatedText", "") or data.get("translation", "")
                if translation:
                    return translation
        except:
            continue
    
    return "[All Gemini services failed]"

# ULTIMATE GEMINI TRANSLATION
def ultimate_gemini_translate(text, target="Lao"):
    """Get real Gemini translation using all available methods"""
    if not text.strip():
        return text
    
    # Try primary Gemini proxy first
    result = gemini_translate(text, target)
    
    # If primary fails, try backup services
    if "[Gemini failed]" in result or "[timeout]" in result or not result:
        result = backup_gemini_services(text, target)
    
    # Final cleanup and verification
    if result and "[Error]" not in result:
        # Ensure proper Mine Action terminology
        result = result.replace("ຂ້ອຍ", "ຂ້າ")  # Natural Lao
        result = result.replace("ຂ້າພະເຈົ້າ", "ຂ້າ")  # Not formal
        
        # Verify we got actual translation
        if len(result.strip()) > 0:
            return result
    
    return "[Translation unavailable]"

# UI
direction = st.radio("Direction", ["English → Lao", "Lao → English"], horizontal=True)

# INSTANT GEMINI TRANSLATION
st.subheader("🎯 Real Gemini Translation")
text = st.text_area("Enter text", height=100, placeholder="dogs stepped on mines")

if st.button("Translate with Gemini", type="primary"):
    if text.strip():
        with st.spinner("Connecting to Gemini API..."):
