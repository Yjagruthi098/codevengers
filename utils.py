#utils.py
import fitz  # PyMuPDF
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests

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

def ask_gemini(context, query, mode="qa", extra_info=None, custom_prompt=None):
    if custom_prompt:
        prompt = custom_prompt
    elif mode == "summary":
        style = extra_info.get("style", "Bullet Points") if extra_info else "Bullet Points"
        if style == "Bullet Points":
            prompt = f"Summarize the following content as bullet points:\n\n{context}"
        elif style == "Executive Summary":
            prompt = f"Write an executive summary of the following content:\n\n{context}"
        elif style == "Technical Summary":
            prompt = f"Write a technical summary of the following content:\n\n{context}"
        else:
            prompt = f"Summarize the following content:\n\n{context}"
    elif mode == "flashcards":
        count = extra_info.get("count", 5) if extra_info else 5
        prompt = f"Create {count} flashcards in 'Question - Answer' format from this:\n\n{context}"
    elif mode == "quiz":
        count = extra_info.get("count", 5) if extra_info else 5
        difficulty = extra_info.get("difficulty", "Medium") if extra_info else "Medium"
        prompt = f"""Generate {count} multiple-choice questions ({difficulty} difficulty) in this exact format:\nQ1. ...\nA) ...\nB) ...\nC) ...\nD) ...\nAnswer: B\nFrom this text:\n\n{context}"""
    else:
        prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nExplain it simply."

    response = model.generate_content(prompt)
    return response.text.strip()

def find_relevant_youtube_video(text):
    prompt = f"""Based on the following content, generate a short, clear YouTube search query to find a relevant educational or explanatory video.

Content:
{text[:2000]}

Return only the search query, no explanation.
"""
    query = ask_gemini(text, "", mode="custom", custom_prompt=prompt)

    # Use YouTube search via Google (no API key needed) — or use official YouTube Data API if preferred
    search_url = f"https://www.googleapis.com/youtube/v3/search"
    api_key = os.getenv("YOUTUBE_API_KEY")  # Add this to your .env
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": api_key
    }

    try:
        res = requests.get(search_url, params=params)
        res.raise_for_status()
        items = res.json().get("items", [])
        if items:
            video_id = items[0]["id"]["videoId"]
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            return None
    except Exception as e:
        print("YouTube fetch error:", e)
        return None
