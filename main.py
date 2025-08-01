#main.py
import streamlit as st
import re
from utils import extract_text_from_pdf, ask_gemini, find_relevant_youtube_video

st.set_page_config(page_title="PDF Q&A (Gemini)", layout="wide")

st.title("📘 AI-Powered PDF Q&A with Gemini")
st.markdown("Upload a PDF, ask questions, and generate summaries, flashcards, or quizzes using Google's Gemini.")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

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
                st.rerun()
            else:
                st.error("Invalid credentials. Please enter a valid name, email, and password (min 6 chars).")

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
                    st.error("Couldn't find a relevant video. Try again or check internet connection.")

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
            if "quiz_data" not in st.session_state:
                st.session_state.quiz_data = None
            if "quiz_answers" not in st.session_state:
                st.session_state.quiz_answers = {}

            def parse_quiz(raw_quiz):
                questions = []
                parts = raw_quiz.strip().split("\n\n")  # split by blank lines
                for part in parts:
                    lines = [line.strip() for line in part.strip().split("\n") if line.strip()]
                    if len(lines) < 6:
                        continue
                    if not lines[0].lower().startswith("q"):
                        continue
                    # Extract question text after "Q<number>."
                    question_text = lines[0].split(".", 1)[1].strip() if "." in lines[0] else lines[0]
                    options = {}
                    try:
                        for opt_line in lines[1:5]:
                            letter, text = opt_line.split(")", 1)
                            options[letter.strip()] = text.strip()
                        answer_line = lines[5]
                        answer = answer_line.split(":", 1)[1].strip()
                    except Exception:
                        continue
                    questions.append({
                        "question": question_text,
                        "options": options,
                        "answer": answer
                    })
                return questions

            if st.button("📝 Generate Quiz"):
                with st.spinner("Generating quiz..."):
                    raw_quiz = ask_gemini(pdf_text, "", mode="quiz")
                    #st.code(raw_quiz, language="text")  # show raw output for debug

                    questions = parse_quiz(raw_quiz)
                    if not questions:
                        st.error("Failed to parse quiz. Please try again or check raw output above.")
                        st.session_state.quiz_data = None
                        st.session_state.quiz_answers = {}
                    else:
                        st.session_state.quiz_data = questions
                        st.session_state.quiz_answers = {}
                        st.success("Quiz generated! Please answer the questions below.")

            if st.session_state.quiz_data:
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
