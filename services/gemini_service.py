import os
from google import genai
from google.genai import types
from pydantic import BaseModel

class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer: str

class AIResponse(BaseModel):
    notes: str
    summary: str
    keywords: list[str]
    quiz: list[QuizQuestion]

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_ai_content(transcript: str):

    MAX_CHARS = 25000

    if len(transcript) > MAX_CHARS:
        transcript = transcript[:MAX_CHARS]

    print(f"Transcript size: {len(transcript)}")

    prompt = f"""
You are an expert university professor.

Based on the following lecture transcript generate:

1. Detailed Study Notes
2. Short Summary
3. Important Keywords
4. 10 Multiple Choice Questions

Transcript:

{transcript}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AIResponse,
        ),
    )

    return response.text