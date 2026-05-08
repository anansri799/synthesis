import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ingestion'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'generation'))

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import json
import shutil

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from ingest import ingest_pdf
from concepts import extract_concepts, save_concepts, get_all_chunks
from generate import generate_problem, save_problem, get_latest_concepts
from db import get_problems_collection

app = FastAPI(title="Synthesis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Synthesis is running"}

@app.post("/ingest")
async def ingest(file: UploadFile = File(...), chunk_type: str = "notes"):
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    ingest_pdf(tmp_path, chunk_type)
    chunks = get_all_chunks()
    concepts = extract_concepts(chunks)
    save_concepts(concepts)
    return {"status": "ingested", "concepts": concepts}

@app.post("/generate")
def generate():
    concepts = get_latest_concepts()
    if not concepts:
        return {"error": "No concepts found. Upload material first."}
    unseen = concepts.get('combinations_unseen', [])
    if not unseen:
        return {"error": "No unseen combinations. Upload more material."}
    pair = unseen[0]
    problem = generate_problem(pair)
    problem_id = save_problem(problem, pair)
    return {
        "problem_id": problem_id,
        "problem": problem['problem'],
        "concepts_tested": problem['concepts_tested'],
        "hints_available": len(problem['hints']),
        "hints_unlocked": 0
    }

@app.get("/hint/{problem_id}/{hint_number}")
def get_hint(problem_id: str, hint_number: int):
    collection = get_problems_collection()
    results = collection.get(ids=[problem_id])
    if not results['documents']:
        return {"error": "Problem not found"}
    problem_data = json.loads(results['documents'][0])
    hints = problem_data.get('hints', [])
    if hint_number < 1 or hint_number > len(hints):
        return {"error": "Invalid hint number"}
    return {
        "hint_number": hint_number,
        "hint": hints[hint_number - 1]
    }

@app.get("/solution/{problem_id}")
def get_solution(problem_id: str):
    collection = get_problems_collection()
    results = collection.get(ids=[problem_id])
    if not results['documents']:
        return {"error": "Problem not found"}
    problem_data = json.loads(results['documents'][0])
    return {"solution": problem_data.get('solution', 'No solution available')}

@app.post("/submit/{problem_id}")
def submit_answer(problem_id: str, answer: dict):
    collection = get_problems_collection()
    results = collection.get(ids=[problem_id])
    if not results['documents']:
        return {"error": "Problem not found"}
    
    problem_data = json.loads(results['documents'][0])
    
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    
    response = client.chat.completions.create(
        model="llama3.2:latest",
        messages=[
            {
                "role": "system",
                "content": """You are a fair tutor grading a student answer.
Compare the student answer to the correct solution and return ONLY valid JSON:
{
  "result": "correct" or "partial" or "incorrect",
  "score": 0 to 100,
  "feedback": "specific feedback on what they got right or wrong",
  "what_they_missed": "what concept or step they missed, or null if correct"
}"""
            },
            {
                "role": "user",
                "content": f"Problem: {problem_data['problem']}\n\nCorrect solution: {problem_data['solution']}\n\nStudent answer: {answer['answer']}"
            }
        ],
        temperature=0.1
    )
    
    raw = response.choices[0].message.content
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        result = json.loads(raw[start:end])
    except:
        result = {"result": "error", "feedback": "Could not grade answer, try again"}
    
    return result