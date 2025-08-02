# main.py
import streamlit as st
import re
from utils import extract_text_from_pdf, ask_gemini, find_relevant_youtube_video

st.set_page_config(page_title="PDF Q&A (Gemini)", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    html, body, .main {
        background-color: #e6f0ff;
    }
    h1 {
        font-size: 3em;
        color: #003366;
        text-align: center;
    }
    .numbered-title {
        font-size: 1.6em;
        font-weight: bold;
        color: #003366;
        margin-top: 2em;
    }
    .stButton > button {
        background-color: #3399ff;
        color: white;
        border-radius: 8px;
        padding: 0.5em 1em;
        font-size: 1em;
        margin-top: 0.8em;
    }
    .question-text {
        font-weight: bold;
        font-size: 18px;
        margin-top: 1em;
    }
    .answer-text {
        background-color: #f7f7f7;
        padding: 1em;
        border-radius: 10px;
        font-size: 16px;
        margin-top: 0.5em;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("📘 AI-Powered PDF Q&A with Gemini")
st.markdown("Upload a PDF, ask questions, and generate flashcards, quizzes, summaries, and outlines using Google's Gemini LLM.")

# --- Authentication ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form("login"):
        st.markdown("### 🔐 Login to Access")
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password(If you are new to this create a new password)", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if name and "@" in email and len(password) >= 6:
                st.session_state.authenticated = True
                st.success(f"Welcome, {name}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

# --- Main UI ---
if st.session_state.authenticated:
    st.markdown("<div class='numbered-title'>1. Upload PDF</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload your PDF here", type=["pdf"])

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.success("✅ PDF parsed successfully!")

        st.markdown("<div class='numbered-title'>2. Ask Questions</div>", unsafe_allow_html=True)
        question = st.text_input("Enter your question")
        if st.button("Get Answer"):
            with st.spinner("Gemini is thinking..."):
                answer = ask_gemini(pdf_text, question, mode="qa")
                st.markdown(f"<div class='question-text'>Q: {question}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='answer-text'>{answer}</div>", unsafe_allow_html=True)
                st.download_button("💾 Download Answer", answer, file_name="answer.txt")

        st.markdown("<div class='numbered-title'>3. YouTube Video Search</div>", unsafe_allow_html=True)
        if st.button("Search YouTube"):
            with st.spinner("Searching..."):
                video_url = find_relevant_youtube_video(pdf_text)
                if video_url:
                    st.video(video_url)
                else:
                    st.error("No relevant video found.")

        st.markdown("<div class='numbered-title'>4. Generate Summary</div>", unsafe_allow_html=True)
        if st.button("📋 Generate Summary"):
            with st.spinner("Summarizing..."):
                summary = ask_gemini(pdf_text, "", mode="summary")
                st.text_area("Summary", summary, height=200)
                st.download_button("💾 Download Summary", summary, file_name="summary.txt")

        st.markdown("<div class='numbered-title'>5. Generate Flashcards</div>", unsafe_allow_html=True)
        st.session_state.flashcard_count = st.number_input("Number of Flashcards", min_value=1, max_value=20, value=5)
        if st.button("🧠 Generate Flashcards"):
            with st.spinner("Generating flashcards..."):
                flashcards = ask_gemini(pdf_text, "", mode="flashcards", extra_info={"count": st.session_state.flashcard_count})
                st.text_area("Flashcards", flashcards, height=200)
                st.download_button("💾 Download Flashcards", flashcards, file_name="flashcards.txt")

        st.markdown("<div class='numbered-title'>6. Generate Quiz</div>", unsafe_allow_html=True)
        st.session_state.quiz_count = st.number_input("Number of Quiz Questions", min_value=1, max_value=20, value=5)

        if "quiz_data" not in st.session_state:
            st.session_state.quiz_data = []
        if "quiz_submitted" not in st.session_state:
            st.session_state.quiz_submitted = False
        if "quiz_answers" not in st.session_state:
            st.session_state.quiz_answers = {}

        if st.button("📝 Generate Quiz"):
            def parse_quiz(raw_quiz):
                pattern = re.compile(
                    r"Q(\d+)\.\s*(.?)\nA\)\s(.?)\nB\)\s(.?)\nC\)\s(.?)\nD\)\s(.?)\nAnswer:?\s([ABCD])",
                    re.DOTALL | re.MULTILINE
                )
                matches = pattern.findall(raw_quiz)
                if not matches:
                    pattern_fallback = re.compile(
                        r"Q(\d+)\.\s*(.?)\nA\)\s(.?)\nB\)\s(.?)\nC\)\s(.?)\nD\)\s(.?)\nAnswer:?\s([ABCD])",
                        re.DOTALL | re.IGNORECASE
                    )
                    matches = pattern_fallback.findall(raw_quiz)
                questions = []
                for m in matches:
                    q_num, question, optA, optB, optC, optD, answer = m
                    questions.append({
                        "question": question.strip(),
                        "options": {
                            "A": optA.strip(),
                            "B": optB.strip(),
                            "C": optC.strip(),
                            "D": optD.strip(),
                        },
                        "answer": answer.strip().upper()
                    })
                return questions

            with st.spinner("Generating quiz..."):
                raw_quiz = ask_gemini(pdf_text, "", mode="quiz", extra_info={"count": st.session_state.quiz_count})
                questions = parse_quiz(raw_quiz)
                if not questions:
                    st.error("Failed to parse quiz.")
                else:
                    st.session_state.quiz_data = questions
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}

        if st.session_state.quiz_data:
            st.markdown("### 📝 Attempt Quiz:")
            for i, q in enumerate(st.session_state.quiz_data):
                user_answer = st.radio(
                    f"Q{i+1}. {q['question']}",
                    ["A", "B", "C", "D"],
                    format_func=lambda x: f"{x}) {q['options'][x]}",
                    key=f"quiz_q{i}"
                )
                st.session_state.quiz_answers[i] = user_answer

            if st.button("✅ Submit Quiz"):
                score = 0
                total = len(st.session_state.quiz_data)
                for i, q in enumerate(st.session_state.quiz_data):
                    if st.session_state.quiz_answers.get(i) == q["answer"]:
                        score += 1
                st.session_state.quiz_submitted = True
                st.session_state.quiz_score = score

        if st.session_state.get("quiz_submitted"):
            score = st.session_state.quiz_score
            total = len(st.session_state.quiz_data)
            st.success(f"✅ Your score: {score} / {total}")

            if score == total:
                st.balloons()
                st.info("🎉 Perfect score! You're a PDF quiz master! 🏆")
            elif score >= total * 0.7:
                st.info("👍 Great job! You passed the quiz!")
            else:
                st.info("📚 Keep practicing and try again!")

            if st.button("🔁 Reset Quiz"):
                st.session_state.quiz_data = []
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()

        st.markdown("<div class='numbered-title'>7. Notebook-style Outline</div>", unsafe_allow_html=True)
        if st.button("📚 Generate Outline"):
            with st.spinner("Generating..."):
                outline = ask_gemini(pdf_text, "", mode="notebook")
                st.text_area("Notebook Outline", outline, height=300)
                st.download_button("💾 Download Outline", outline, file_name="notebook_outline.txt")

    st.divider()
    if st.button("🔐 Logout"):
        st.session_state.authenticated = False
        st.rerun()
