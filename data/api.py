import os
import re
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from askllm import ask_question

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    model: str = "gpt"

def format_answer(text: str) -> str:
    text = text.strip()
    # Strip trailing whitespace from each line (prevents markdown <br> artefacts)
    lines = [l.rstrip() for l in text.split('\n')]
    text = '\n'.join(lines)
    # Normalize to exactly one blank line between numbered list items
    text = re.sub(r'\n+(\d+\.)', r'\n\n\1', text)
    return text

@app.post("/ask")
def ask(req: QuestionRequest):
    answer = ask_question(req.question, model=req.model)
    # print(repr(answer))
    return {"answer": format_answer(answer)}
