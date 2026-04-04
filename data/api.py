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
    lines = text.split('\n')

    # Remove blank lines and strip trailing whitespace (prevents markdown <br> from trailing spaces)
    non_blank = [l.rstrip() for l in lines if l.strip()]

    result = []
    for i, line in enumerate(non_blank):
        prev_stripped = non_blank[i - 1].strip() if i > 0 else ''

        # Blank line after any intro line ending with ':'
        if i > 0 and prev_stripped.endswith(':'):
            result.append('')
        # Blank line before the closing sentence (last line)
        elif i == len(non_blank) - 1:
            result.append('')

        result.append(line)

    return '\n'.join(result)

@app.post("/ask")
def ask(req: QuestionRequest):
    answer = ask_question(req.question, model=req.model)
    formatted = format_answer(answer)
    print("=== RAW ===")
    print(repr(answer[:300]))
    print("=== FORMATTED ===")
    print(repr(formatted[:300]))
    return {"answer": formatted}
