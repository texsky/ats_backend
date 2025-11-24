# main.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pdfminer.high_level import extract_text
import re
from collections import Counter

app = FastAPI()

# Allow React frontend to call this API
origins = [
    "http://localhost:3000",  # React dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Function to extract text from resume
# -------------------------
def extract_resume_text(file_path):
    if file_path.endswith(".pdf"):
        text = extract_text(file_path)
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise ValueError("Unsupported file format")
    return text.lower()

# -------------------------
# ATS Score Function
# -------------------------
def ats_score(resume_text, job_description):
    resume_words = re.findall(r'\b\w+\b', resume_text.lower())
    jd_words = re.findall(r'\b\w+\b', job_description.lower())

    resume_counter = Counter(resume_words)
    jd_counter = Counter(jd_words)

    matched_keywords = sum(min(resume_counter[word], jd_counter[word]) for word in jd_counter)
    total_keywords = sum(jd_counter.values())

    score = (matched_keywords / total_keywords) * 100
    return round(score, 2)

# -------------------------
# API Endpoint
# -------------------------
@app.post("/upload_resume/")
async def upload_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    # Save uploaded file
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Extract text & calculate score
    try:
        resume_text = extract_resume_text(file_location)
        score = ats_score(resume_text, job_description)
        result = {
            "score": score,
            "status": "likely shortlisted" if score > 70 else "needs optimization"
        }
    except Exception as e:
        result = {"error": str(e)}

    return result
