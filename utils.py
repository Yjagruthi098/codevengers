import fitz  # PyMuPDF
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")

def extract_text_from_pdf(file):
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    return " ".join(page.get_text() for page in pdf)

def ask_gemini(context, query, mode="qa"):
    if mode == "summary":
        prompt = f"Summarize the following content:\n\n{context}"
    elif mode == "flashcards":
        prompt = f"Create 5 flashcards in 'Question - Answer' format from this:\n\n{context}"
    elif mode == "quiz":
        prompt = f"Generate 5 multiple-choice quiz questions from this:\n\n{context}"
    else:
        prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nExplain it simply."

    response = model.generate_content(prompt)
    return response.text.strip()
