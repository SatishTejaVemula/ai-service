
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
import json
import traceback
from pydantic import BaseModel
from typing import List
from services.gemini_service import client
from services.ppt_service import extract_ppt_text

from services.whisper_service import transcribe
from services.gemini_service import generate_ai_content

class Message(BaseModel):

    role: str

    content: str

class ChatRequest(BaseModel):

    transcript: str = ""

    notes: str = ""

    summary: str = ""

    question: str

    history: List[Message] = []

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):

    try:

        filename = os.path.basename(audio.filename or "upload.wav")
        path = os.path.join(UPLOAD_DIR, filename)

        with open(path, "wb") as buffer:

            shutil.copyfileobj(audio.file, buffer)

        start = time.time()
        transcript = transcribe(path)
        print(f"Whisper took {time.time() - start:.2f} seconds")

        if isinstance(transcript, list):
            transcript = " ".join(transcript)

        start = time.time()
        ai = generate_ai_content(transcript)
        print(f"Gemini took {time.time() - start:.2f} seconds")

        if ai is None:
            return {"error": "Unable to generate AI content"}

        ai = ai.replace("```json", "")
        ai = ai.replace("```", "")

        ai = json.loads(ai)

        return {

            "transcript": transcript,

            "notes": ai["notes"],

            "summary": ai["summary"],

            "keywords": ", ".join(ai["keywords"]),

            "quiz": json.dumps(ai["quiz"])

        }

    except Exception:

        traceback.print_exc()

        return {

            "error": "Unable to process lecture"

        }
    
@app.post("/chat")
async def chat(request: ChatRequest):

    try:

        history_text = ""

        for msg in request.history:

            if msg.role == "user":

                history_text += f"Student: {msg.content}\n"

            else:

                history_text += f"AIMate: {msg.content}\n"


        has_lecture_context = bool(
            request.transcript.strip()
            or request.notes.strip()
            or request.summary.strip()
        )


        if has_lecture_context:

            prompt = f"""
You are AIMate, an intelligent university professor and study assistant.

The student is asking questions about a lecture.

Use ONLY the lecture information provided below.

========================
LECTURE TRANSCRIPT
========================

{request.transcript}

========================
AI NOTES
========================

{request.notes}

========================
SUMMARY
========================

{request.summary}

========================
CONVERSATION HISTORY
========================

{history_text}

========================
CURRENT QUESTION
========================

{request.question}

Rules:

1. Remember the previous conversation.
2. Words like "it", "that", "previous topic", "its", "them", etc. refer to the conversation history.
3. Answer using only the lecture transcript, notes and summary.
4. Never invent information about the lecture.
5. If the lecture doesn't contain the answer, say:
"I couldn't find that information in this lecture."
6. Explain concepts like a university professor.
7. Use Markdown formatting.
8. Keep the answer clear and easy to understand.
"""

        else:

            prompt = f"""
You are AIMate, an intelligent university study assistant.

You help university students understand academic concepts.

========================
CONVERSATION HISTORY
========================

{history_text}

========================
CURRENT QUESTION
========================

{request.question}

Rules:

1. Remember the previous conversation.
2. Answer clearly and accurately.
3. Explain concepts like a university professor.
4. Use Markdown formatting when useful.
5. Keep explanations easy to understand.
6. Do not claim that information comes from a lecture when no lecture is provided.
"""


        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )


        return {
            "answer": response.text
        }


    except Exception as e:

        error = str(e)

        print("CHAT ERROR:", error)

        if "RESOURCE_EXHAUSTED" in error or "429" in error:

            return {
                "answer": "⚠️ AIMate AI is temporarily unavailable because the AI limit has been reached. Please try again later."
            }


        return {
            "answer": "⚠️ Something went wrong while generating the AI response."
        }
        
@app.post("/process-ppt")
async def process_ppt(ppt: UploadFile = File(...)):

    try:

        print("=================================")
        print("Step 1 - Request received")
        print("=================================")

        start = time.time()

        filename = os.path.basename(ppt.filename or "upload.pptx")

        path = os.path.join(UPLOAD_DIR, filename)

        with open(path, "wb") as buffer:
            shutil.copyfileobj(ppt.file, buffer)

        text = extract_ppt_text(path)

        print(f"Step 2 - PPT extracted in {time.time() - start:.2f} seconds")

        start = time.time()

        print("Step 3 - Calling Gemini...")

        ai = generate_ai_content(text)

        print(f"Step 4 - Gemini finished in {time.time() - start:.2f} seconds")

        if ai is None:
            return {
                "error": "Unable to generate AI content"
            }

        print("========== GEMINI RESPONSE ==========")
        print(ai)
        print("=====================================")
        

        ai = json.loads(ai)

        return {

            "transcript": text,

            "notes": ai.get("notes") or ai.get("detailed_study_notes", ""),

            "summary": ai.get("summary") or ai.get("short_summary", ""),

            "keywords": ", ".join(
                ai.get("keywords") or ai.get("important_keywords", [])
            ),

            "quiz": json.dumps(
               ai.get("quiz") or ai.get("multiple_choice_questions", [])
            )

}

    except Exception:

        traceback.print_exc()

        return {

            "error": "Unable to process PPT"

        }