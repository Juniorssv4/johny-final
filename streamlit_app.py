import streamlit as st

import google.generativeai as genai

from google.api_core.exceptions import ResourceExhausted

import time

import os

import json

# --- Config ---

st.set_page_config(page_title="Johnny – NPA Lao Translator", layout="centered")

st.title("Johnny – NPA Lao Translator")

# API Key from Streamlit secrets

if "GOOGLE_API_KEY" not in st.secrets:

    st.error("API key not found in secrets. Add GOOGLE_API_KEY to Streamlit secrets.")

    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Model (use flash for speed/cost, or pro for better quality)

MODEL_NAME = "gemini-1.5-flash"  # or "gemini-1.5-pro"

# Load glossary (persistent across sessions via session_state or file if needed)

if "glossary" not in st.session_state:

    st.session_state.glossary = {}  # {english: lao} or bidirectional

# --- Sidebar ---

with st.sidebar:

    st.header("Direction")

    direction = st.radio("Translate direction", options=["English → Lao", "Lao → English"], index=0)

    st.header("Active glossary")

    st.write(f"{len(st.session_state.glossary)} terms")

    if st.session_state.glossary:

        for eng, lao in st.session_state.glossary.items():

            st.write(f"**{eng}** → **{lao}**")

# Tabs

tab1, tab2 = st.tabs(["Translate Text", "Translate File"])

# --- Helper functions ---

def apply_glossary(text, glossary, src_lang):

    """Simple replacement using glossary (case insensitive for English)"""

    if src_lang == "en":

        for eng, lao in glossary.items():

            text = text.replace(eng.lower(), lao).replace(eng.title(), lao).replace(eng.upper(), lao)

    else:

        for eng, lao in glossary.items():

            text = text.replace(lao, eng)

    return text

def translate_with_retry(prompt):

    """Translate with retry on ResourceExhausted (429 quota)"""

    max_retries = 5

    retry_delay = 5  # start with 5 seconds

    for attempt in range(max_retries):

        try:

            model = genai.GenerativeModel(MODEL_NAME)

            response = model.generate_content(prompt)

            return response.text.strip()

        except ResourceExhausted as e:

            if attempt == max_retries - 1:

                raise e  # final fail

            st.warning(f"Rate limit hit (attempt {attempt+1}/{max_retries}). Retrying in {retry_delay} seconds...")

            time.sleep(retry_delay)

            retry_delay *= 2  # exponential backoff

        except Exception as e:

            st.error(f"Unexpected error: {str(e)}")

            return "[Translation failed – try later]"

# --- Text Translation Tab ---

with tab1:

    st.write("Enter text to translate")

    user_text = st.text_area("", placeholder="Type or paste text here...", height=150)

    if st.button("Translate Text"):

        if not user_text.strip():

            st.warning("Please enter some text.")

        else:

            with st.spinner("Translating..."):

                # Determine languages

                src_lang = "en" if direction == "English → Lao" else "lo"

                target_lang = "Lao" if direction == "English → Lao" else "English"

                # Build prompt

                prompt = f"""

                Translate the following text from {src_lang.upper()} to {target_lang}:

                Only output the translation, nothing else.

                Text: "{user_text}"

                """

                try:

                    translation = translate_with_retry(prompt)

                    # Apply glossary after translation

                    translation = apply_glossary(translation, st.session_state.glossary, src_lang)

                    st.success("Translation:")

                    st.markdown(f"**{translation}**")

                except ResourceExhausted:

                    st.error("Translation timed out after retries — rate limit delay in Tier 1. Try again in 5 minutes.")

                    st.info("If this persists even after billing, submit a quota increase request in Google Cloud Console > Quotas > Generative Language API.")

                except Exception:

                    st.error("[Translation failed – try later]")

# --- Teach new term ---

st.divider()

new_term = st.text_input("➕ Teach Johnny a new term (saved forever)")

col1, col2 = st.columns(2)

with col1:

    eng_term = st.text_input("English term")

with col2:

    lao_term = st.text_input("Lao term (ພາສາລາວ)")

if st.button("Save term to glossary"):

    if eng_term and lao_term:

        st.session_state.glossary[eng_term.strip()] = lao_term.strip()

        st.success(f"Saved: {eng_term} → {lao_term}")

        st.rerun()

    else:

        st.warning("Enter both terms.")

# --- File tab placeholder (expand later if needed) ---

with tab2:

    st.info("File translation coming soon! For now, use Text tab.")

st.caption("Johnny uses Gemini API. Glossary improvements are user-powered. 🚀")
 
