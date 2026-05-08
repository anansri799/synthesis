import os
import json
import re
import sys
sys.path.append('../ingestion')
from openai import OpenAI
from db import get_concepts_collection, get_problems_collection
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def get_latest_concepts():
    collection = get_concepts_collection()
    try:
        results = collection.get(ids=["latest"])
        if results['documents']:
            return json.loads(results['documents'][0])
    except:
        return None

def generate_problem(concept_pair):
    response = client.chat.completions.create(
        model="llama3.2:latest",
        messages=[
            {
                "role": "system",
                "content": """You are an expert tutor that creates challenging but fair problems.
Given two concepts, create a problem requiring BOTH concepts.
Return ONLY valid JSON, no backticks, no markdown, no special characters or backslashes.
Use plain English only inside JSON strings.
Exact format:
{
  "problem": "problem statement in plain text",
  "concepts_tested": ["concept 1", "concept 2"],
  "hints": [
    "hint 1 - conceptual nudge only",
    "hint 2 - structural guidance",
    "hint 3 - near solution"
  ],
  "solution": "full solution in plain text"
}"""
            },
            {
                "role": "user",
                "content": f"Create a problem combining: {concept_pair[0]} and {concept_pair[1]}"
            }
        ]
    )
    raw = response.choices[0].message.content
    start = raw.find('{')
    end = raw.rfind('}') + 1
    cleaned = raw[start:end]
    cleaned = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', cleaned)
    return json.loads(cleaned)

def save_problem(problem_data, concept_pair):
    collection = get_problems_collection()
    import time
    problem_id = str(int(time.time()))
    collection.add(
        documents=[json.dumps(problem_data)],
        metadatas=[{"concept_pair": str(concept_pair), "hints_unlocked": 0}],
        ids=[problem_id]
    )
    return problem_id

if __name__ == "__main__":
    concepts = get_latest_concepts()
    if not concepts:
        print("No concepts found. Run concepts.py first.")
        exit()

    unseen = concepts.get('combinations_unseen', [])
    if not unseen:
        print("No unseen combinations. Ingest more material.")
        exit()

    pair = unseen[0]
    print(f"\nGenerating problem for: {pair[0]} + {pair[1]}\n")
    
    problem = generate_problem(pair)
    problem_id = save_problem(problem, pair)
    
    print(f"Problem #{problem_id}:")
    print(f"\n{problem['problem']}\n")
    print("Hints available (unlockable):")
    for i in range(len(problem['hints'])):
        print(f"  Hint {i+1}: [locked]")