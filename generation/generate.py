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
                "content": """You are an expert tutor. Create a problem combining two concepts.
You MUST respond with ONLY a JSON object. No backticks, no markdown, no extra text.
Use simple plain English. No math symbols, no backslashes, no special characters.
Format:
{
  "problem": "problem statement here",
  "concepts_tested": ["concept 1", "concept 2"],
  "hints": ["hint 1", "hint 2", "hint 3"],
  "solution": "solution here"
}"""
            },
            {
                "role": "user",
                "content": f"Create a simple problem combining: {concept_pair[0]} and {concept_pair[1]}. Keep all text very simple, no special characters."
            }
        ],
        temperature=0.1
    )
    raw = response.choices[0].message.content
    # Try multiple JSON extraction strategies
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end])
    except:
        try:
            import re
            cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', raw)
            cleaned = re.sub(r'\\(?!["\\/bfnrtu])', '', cleaned)
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            return json.loads(cleaned[start:end])
        except Exception as e:
            return {
                "problem": f"Combine these concepts: {concept_pair[0]} and {concept_pair[1]}",
                "concepts_tested": concept_pair,
                "hints": ["Think about the first concept", "Now apply the second concept", "Combine both approaches"],
                "solution": "Solution generation failed - try again"
            }

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