import os
import json
import re
from openai import OpenAI
from db import get_chunks_collection, get_concepts_collection
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def get_all_chunks():
    collection = get_chunks_collection()
    results = collection.get()
    return list(zip(results['ids'], results['documents'], 
                   [m['chunk_type'] for m in results['metadatas']]))

def extract_concepts(chunks):
    combined = "\n\n".join([f"[{ctype}] {content}" for _, content, ctype in chunks])
    
    response = client.chat.completions.create(
        model="llama3.2:latest",
        messages=[
            {
                "role": "system",
                "content": """You are an expert at analyzing study material.
Extract key concepts from the provided notes and problems.
Return ONLY valid JSON, no backticks, no markdown, no special characters.
Exact format:
{
  "concepts": ["concept 1", "concept 2"],
  "combinations_seen": [["concept A", "concept B"]],
  "combinations_unseen": [["concept X", "concept Y"]]
}"""
            },
            {
                "role": "user",
                "content": f"Analyze this study material and identify concept pairs that appear in notes but have NOT been combined in any problem yet. These are the most important gaps.\n\n{combined}"
            }
        ]
    )
    
    raw = response.choices[0].message.content
    start = raw.find('{')
    end = raw.rfind('}') + 1
    cleaned = raw[start:end]
    cleaned = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', cleaned)
    return json.loads(cleaned)

def save_concepts(concepts_data):
    collection = get_concepts_collection()
    collection.add(
        documents=[json.dumps(concepts_data)],
        ids=["latest"]
    )
    print("Concepts saved.")

if __name__ == "__main__":
    print("Fetching chunks...")
    chunks = get_all_chunks()
    print(f"Analyzing {len(chunks)} chunks...")
    concepts = extract_concepts(chunks)
    print("\nConcepts found:")
    print(json.dumps(concepts, indent=2))
    save_concepts(concepts)