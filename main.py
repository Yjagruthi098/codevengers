import streamlit as st
import re
from utils import extract_text_from_pdf, ask_gemini, find_relevant_youtube_video

st.set_page_config(page_title="PDF Q&A (Gemini)", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #e6f0ff;
    }
    h1, h3, h4 {
        color: #003366;
    }
    .question-text {
        font-weight: bold;
        color: #000000;
        font-size: 16px;
        margin-bottom: 6px;
    }
    .answer-text {
        color: #333333;
        background-color: #f7f7f7;
        padding: 0.75em;
        border-radius: 8px;
        font-size: 15px;
        line-height: 1.5;
    }
    button[kind="primary"] {
        background-color: #3399ff !important;
        color: white !important;
        border-radius: 8px;
        padding: 0.5em 1em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📘 AI-Powered PDF Q&A with Gemini")
st.markdown("Upload a PDF, ask questions, and generate summaries, flashcards, or quizzes using Google's Gemini.")

# Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.form("login"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password(Create a new password)", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if name and "@" in email and len(password) >= 6:
                st.session_state.authenticated = True
                st.success(f"Welcome, {name}!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please enter a valid name, email, and password (min 6 chars).")

# Main interface after login
if st.session_state.authenticated:
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.success("✅ PDF parsed successfully!")

        st.markdown("### 🎥 Relevant YouTube Video")
        if st.button("Find Related Video"):
            with st.spinner("Searching YouTube..."):
                video_url = find_relevant_youtube_video(pdf_text)
                if video_url:
                    st.video(video_url)
                else:
                    st.warning("No relevant video found.")

        st.success("✅ PDF parsed successfully!")

        # 1. Summary
        st.markdown("### 📋 Generate Summary")
        summary_mode = st.selectbox("Summary Style", ["Bullet Points", "Executive Summary", "Technical Summary"], key="summary_mode")
        if "summary" not in st.session_state:
            if st.button("Generate Summary"):
                with st.spinner("Summarizing..."):
                    st.session_state.summary = ask_gemini(pdf_text, "", mode="summary", extra_info={"style": summary_mode})
        if "summary" in st.session_state:
            st.text_area("Summary", st.session_state.summary, height=200)
            st.download_button("💾 Download Summary", st.session_state.summary, file_name="summary.txt")

        # 2. Flashcards
        st.markdown("### 🧠 Generate Flashcards")
        if "flashcard_count" not in st.session_state:
            st.session_state.flashcard_count = 5
        st.session_state.flashcard_count = st.number_input(
            "Number of Flashcards", min_value=1, max_value=20,
            value=st.session_state.flashcard_count, step=1, key="flashcard_count_input"
        )
        if "flashcards" not in st.session_state:
            if st.button("Generate Flashcards"):
                with st.spinner("Generating flashcards..."):
                    st.session_state.flashcards = ask_gemini(
                        pdf_text, "", mode="flashcards",
                        extra_info={"count": st.session_state.flashcard_count}
                    )
        if "flashcards" in st.session_state:
            st.text_area("Flashcards", st.session_state.flashcards, height=200)
            st.download_button("💾 Download Flashcards", st.session_state.flashcards, file_name="flashcards.txt")

        # 3. Quiz
        st.markdown("### 📝 Generate Quiz")
        quiz_difficulty = st.selectbox("Quiz Difficulty", ["Easy", "Medium", "Hard"], key="quiz_difficulty")
        if "quiz_count" not in st.session_state:
            st.session_state.quiz_count = 5
        st.session_state.quiz_count = st.number_input(
            "Number of Quiz Questions", min_value=1, max_value=20,
            value=st.session_state.quiz_count, step=1, key="quiz_count_input"
        )
        if "quiz_data" not in st.session_state:
            def parse_quiz(raw_quiz):
                import re
                pattern = re.compile(
                    r"Q(\d+)\.\s*(.*?)\nA\)\s*(.*?)\nB\)\s*(.*?)\nC\)\s*(.*?)\nD\)\s*(.*?)\nAnswer:\s*([ABCD])",
                    re.DOTALL | re.MULTILINE
                )
                matches = pattern.findall(raw_quiz)
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
                        "answer": answer.strip()
                    })
                return questions
            if st.button("Generate Quiz"):
                with st.spinner("Generating quiz..."):
                    raw_quiz = ask_gemini(
                        pdf_text, "", mode="quiz",
                        extra_info={"count": st.session_state.quiz_count, "difficulty": quiz_difficulty}
                    )
                    questions = parse_quiz(raw_quiz)
                    if not questions:
                        st.error("Failed to parse quiz.")
                        st.session_state.quiz_data = None
                        st.session_state.quiz_answers = {}
                    else:
                        st.session_state.quiz_data = questions[:st.session_state.quiz_count]
                        st.session_state.quiz_answers = {}
                        st.success("Quiz generated! Please answer below.")
        if "quiz_data" in st.session_state:
            st.markdown("### 📝 Attempt the Quiz:")
            for i, q in enumerate(st.session_state.quiz_data):
                user_answer = st.radio(
                    f"Q{i+1}. {q['question']}",
                    options=["A", "B", "C", "D"],
                    format_func=lambda x: f"{x}) {q['options'][x]}",
                    key=f"quiz_q{i}"
                )
                st.session_state.quiz_answers[i] = user_answer

            if st.button("Submit Quiz"):
                score = 0
                total = len(st.session_state.quiz_data)
                for i, q in enumerate(st.session_state.quiz_data):
                    if st.session_state.quiz_answers.get(i) == q["answer"]:
                        score += 1
                st.success(f"Your score: {score} / {total}")

                if score == total:
                    st.balloons()
                    st.info("🎉 Perfect score! You're a PDF quiz master! 🏆")
                elif score >= total * 0.7:
                    st.info("👍 Great job! You passed the quiz!")
                else:
                    st.info("📚 Keep practicing and try again!")

                if st.button("Reset Quiz"):
                    st.session_state.quiz_data = None
                    st.session_state.quiz_answers = {}

    if st.button("🔐 Logout"):
        st.session_state.authenticated = False
        st.rerun()
