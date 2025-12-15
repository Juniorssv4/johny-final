import streamlit as st

import google.generativeai as genai

from google.api_core.exceptions import ResourceExhausted

import time

# --- Page Config ---

st.set_page_config(page_title="Johnny – NPA Lao Translator", layout="centered")

st.title("Johnny – NPA Lao Translator")

# --- Sidebar: Debug Secrets Status ---

st.sidebar.header("🔧 Debug: Secrets Status")

api_key = None

if hasattr(st, "secrets") and st.secrets:

    st.sidebar.success("Secrets file loaded successfully!")

    st.sidebar.code(f"Available keys: {list(st.secrets.keys())}")

    if "GOOGLE_API_KEY" in st.secrets:

        api_key = st.secrets["GOOGLE_API_KEY"].strip()

        if api_key and len(api_key) > 10 and api_key.startswith("AIza"):

            st.sidebar.success("Valid Gemini API key detected! 🚀")

        else:

            st.sidebar.warning("Key found but looks invalid or empty")

    else:

        st.sidebar.error('"GOOGLE_API_KEY" not found in secrets')

else:

    st.sidebar.error("No secrets loaded at all! 😱 Check Streamlit settings or .streamlit/secrets.toml")

# Stop if no valid key

if not api_key:

    st.error("⚠️ No valid GOOGLE_API_KEY found.")

    st.info("""

    To fix:

    1. Go to app Settings → Secrets

    2. Add exactly: GOOGLE_API_KEY = "your-key-here"

    3. Save and Reboot

    OR create .streamlit/secrets.toml in your GitHub repo with the same line.

    """)

    st.stop()

# Configure Gemini

genai.configure(api_key=api_key)

# Model

MODEL_NAME = "gemini-1.5-flash"  # Fast & cheap. Change to "gemini-1.5-pro" for better quality

# Glossary (saved in session)

if "glossary" not in st.session_state:

    st.session_state.glossary = {}

# --- Sidebar Controls ---

with st.sidebar:

    st.header("Translation Direction")

    direction = st.radio("", options=["English → Lao", "Lao → English"], index=0)

    st.header(f"Active Glossary ({len(st.session_state.glossary)} terms)")

    if st.session_state.glossary:

        for eng, lao in st.session_state.glossary.items():

            st.write(f"**{eng}** → **{lao}**")

    else:

        st.info("No terms saved yet")

# --- Tabs ---

tab1, tab2 = st.tabs(["Translate Text", "Translate File"])

# --- Helper: Apply Glossary ---

def apply_glossary(text, src_is_english):

    if src_is_english:

        for eng, lao in st.session_state.glossary.items():

            text = text.replace(eng, lao)

            text = text.replace(eng.lower(), lao)

            text = text.replace(eng.title(), lao)

    else:

        for eng, lao in st.session_state.glossary.items():

            text = text.replace(lao, eng)

    return text

# --- Helper: Translate with Retry ---

def translate_with_retry(prompt):

    max_retries = 6

    delay = 5

    for attempt in range(max_retries):

        try:

            model = genai.GenerativeModel(MODEL_NAME)

            response = model.generate_content(prompt)

            return response.text.strip()

        except ResourceExhausted:

            if attempt == max_retries - 1:

                raise

            st.warning(f"Rate limit hit. Retrying in {delay}s... ({attempt+1}/{max_retries})")

            time.sleep(delay)

            delay *= 2

        except Exception as e:

            st.error(f"API Error: {str(e)}")

            return None

    return None

# --- Text Translation Tab ---

with tab1:

    st.write("Enter text to translate")

    user_text = st.text_area("", placeholder="Type or paste here...", height=150, label_visibility="collapsed")

    if st.button("Translate Text", type="primary"):

        if not user_text.strip():

            st.warning("Please enter some text.")

        else:

            with st.spinner("Translating..."):

                src = "English" if direction == "English → Lao" else "Lao"

                target = "Lao" if direction == "English → Lao" else "English"

                prompt = f"""

                Translate only the text below from {src} to {target}.

                Output ONLY the translation, no explanations.

                Text: "{user_text}"

                """

                try:

                    translation = translate_with_retry(prompt)

                    if translation:

                        # Apply custom glossary

                        translation = apply_glossary(translation, direction == "English → Lao")

                        st.success("Translation:")

                        st.markdown(f"**{translation}**")

                    else:

                        st.error("[Translation failed – try later]")

                except ResourceExhausted:

                    st.error("Translation timed out – rate limit in Tier 1.")

                    st.info("Submit a quota increase in Google Cloud Console → Quotas → Generative Language API to unlock higher limits.")

                except Exception as e:

                    st.error(f"Unexpected error: {e}")

# --- Teach New Term ---

st.divider()

st.subheader("➕ Teach Johnny a new term (saved forever)")

col1, col2 = st.columns(2)

with col1:

    eng_term = st.text_input("English term")

with col2:

    lao_term = st.text_input("Lao term (ພາສາລາວ)")

if st.button("Save to glossary"):

    if eng_term.strip() and lao_term.strip():

        st.session_state.glossary[eng_term.strip()] = lao_term.strip()

        st.success(f"Saved: **{eng_term.strip()}** → **{lao_term.strip()}**")

        st.rerun()

    else:

        st.warning("Please fill both fields.")

# --- File Tab (Placeholder) ---

with tab2:

    st.info("File upload translation coming soon! Use Text tab for now.")

# --- Footer ---

st.caption("Johnny uses Google Gemini API • Glossary is user-powered • Made with ❤️ for Lao speakers")
For Sale Page
 
