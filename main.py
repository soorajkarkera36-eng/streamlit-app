import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
import pandas as pd
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Recruiter AI (Free Tier)", layout="wide")

# --- MODEL CONFIG ---
FLASH_MODEL = "gemini-2.5-flash-lite"   # <-- UPDATED
PRO_MODEL = "gemini-2.5-pro"           # optional if you use later

# --- HELPER FUNCTIONS ---
def extract_text(file):
    text = ""
    try:
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t
        elif file.name.endswith('.docx'):
            doc = docx.Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            text = file.read().decode("utf-8")
    except Exception as e:
        return f"Error reading file: {e}"
    return text


def get_gemini_response(prompt, api_key, model_name):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        if response.candidates:
            return response.candidates[0].content.parts[0].text

        return "No response from model."

    except Exception as e:
        return f"Error: {e}"


# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("Google API Key", type="password")
    st.caption("Get it free: aistudio.google.com")
    st.info("Using Gemini 2.5 Flash Lite")

# --- MAIN APP ---
st.title("🚀 Smart Recruiter (Gemini 2.5 Flash Lite)")

if not api_key:
    st.warning("Please enter API Key.")
    st.stop()

tab1, tab2 = st.tabs(["1️⃣ Strategy Builder", "2️⃣ Bulk Screener"])

# --- TAB 1 ---
with tab1:
    st.header("Define the Real Requirement")

    col1, col2 = st.columns(2)
    with col1:
        jd_text = st.text_area("Paste JD Here", height=150)
        role = st.text_input("Role Title")

    with col2:
        sample_cv = st.file_uploader("Upload Gold Standard CV")
        no_poach = st.text_input("No Poach Companies")

    if st.button("Generate Strategy"):
        if jd_text and sample_cv:
            with st.spinner("Building hiring intelligence..."):
                cv_text = extract_text(sample_cv)

                prompt = f"""
                Analyze this JD and the Sample CV for the role of {role}.
                If the Sample CV has different skills than the JD, assume the Sample CV is the CORRECT requirement.

                Job Description:
                {jd_text}

                Sample CV:
                {cv_text}

                Tasks:
                1. Create a Revised JD Logic.
                2. List 10 Key Search Keywords.
                3. Create a Boolean Search String (exclude: {no_poach}).
                """

                result = get_gemini_response(prompt, api_key, FLASH_MODEL)

                st.session_state['logic'] = result
                st.success("Strategy Created!")
                st.write(result)
        else:
            st.warning("Please provide JD and Sample CV.")


# --- TAB 2 ---
with tab2:
    st.header("Bulk Resume Scoring")

    if 'logic' in st.session_state:
        files = st.file_uploader("Upload Bulk Resumes", accept_multiple_files=True)

        if st.button("Screen All") and files:
            results = []
            bar = st.progress(0)
            status = st.empty()

            for i, file in enumerate(files):
                status.text(f"Processing {i+1}/{len(files)}: {file.name}")

                resume_text = extract_text(file)

                prompt = f"""
                Role Logic:
                {st.session_state['logic']}

                Candidate Resume:
                {resume_text}

                Task:
                Score from 0-100 based on match.

                Output format strictly:
                Score: number | Reason: short explanation
                """

                output = get_gemini_response(prompt, api_key, FLASH_MODEL)

                try:
                    score = output.split("Score:")[1].split("|")[0].strip()
                    reason = output.split("Reason:")[1].strip()
                except:
                    score = "0"
                    reason = output

                results.append({
                    "Resume": file.name,
                    "Score": score,
                    "Reason": reason
                })

                # Lite model → usually faster → you can reduce sleep slightly
                time.sleep(3)

                bar.progress((i + 1) / len(files))

            st.success("Done!")
            df = pd.DataFrame(results)
            st.dataframe(df)

    else:
        st.warning("Go to Tab 1 and generate strategy first.")