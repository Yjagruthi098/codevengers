import streamlit as st
from utils import extract_text_from_pdf, ask_gemini

st.set_page_config(page_title="PDF Q&A (Gemini)", layout="wide")

st.title("📘 AI-Powered PDF Q&A with Gemini")
st.markdown("Upload a PDF, ask questions, and generate summaries, flashcards, or quizzes using Google's Gemini.")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- Lightweight Auth ---
if not st.session_state.authenticated:
    with st.form("login"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if name and "@" in email and len(password) >= 6:
                st.session_state.authenticated = True
                st.success(f"Welcome, {name}!")
            else:
                st.error("Invalid credentials. Try again.")

# --- Main App ---
if st.session_state.authenticated:
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.success("✅ PDF parsed successfully!")

        st.markdown("### 🔍 Ask a Question")
        question = st.text_input("Enter your question about the PDF")
        if st.button("Get Answer"):
            with st.spinner("Gemini is thinking..."):
                answer = ask_gemini(pdf_text, question, mode="qa")
                st.text_area("Answer", answer, height=200)
                st.download_button("💾 Download Answer", answer, file_name="answer.txt")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 Generate Summary"):
                with st.spinner("Summarizing..."):
                    summary = ask_gemini(pdf_text, "", mode="summary")
                    st.text_area("Summary", summary, height=200)
                    st.download_button("💾 Download Summary", summary, file_name="summary.txt")

        with col2:
            if st.button("🧠 Generate Flashcards"):
                with st.spinner("Generating flashcards..."):
                    flashcards = ask_gemini(pdf_text, "", mode="flashcards")
                    st.text_area("Flashcards", flashcards, height=200)
                    st.download_button("💾 Download Flashcards", flashcards, file_name="flashcards.txt")

        with col3:
            if st.button("📝 Generate Quiz"):
                with st.spinner("Generating quiz..."):
                    quiz = ask_gemini(pdf_text, "", mode="quiz")
                    st.text_area("Quiz", quiz, height=200)
                    st.download_button("💾 Download Quiz", quiz, file_name="quiz.txt")

    if st.button("🔐 Logout"):
        st.session_state.authenticated = False
        st.experimental_rerun()
