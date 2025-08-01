#utils.py
import fitz  # PyMuPDF
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

# Use the Gemini model; you can adjust model name as needed
model = genai.GenerativeModel("gemini-2.5-flash")

def extract_text_from_pdf(file):
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join(page.get_text() for page in pdf)

def ask_gemini(context, query, mode="qa"):
    if mode == "summary":
        prompt = f"Summarize the following content:\n\n{context}"
    elif mode == "flashcards":
        prompt = f"Create 5 flashcards in 'Question - Answer' format from this:\n\n{context}"
    elif mode == "quiz":
        # Stricter quiz prompt for consistent formatting
        prompt = f"""Generate 5 multiple-choice questions in this exact format, numbered Q1., Q2., etc., with options starting with A), B), C), D), and the correct answer at the end as "Answer: <Letter>":

Example:

Q1. What is the capital of France?
A) Berlin
B) Paris
C) Rome
D) Madrid
Answer: B

Now generate the quiz from this text:

{context}
"""
    else:
        prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nExplain it simply."

    response = model.generate_content(prompt)
    return response.text.strip()
