import os
import json
from openai import OpenAI
from db import get_connection
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def get_all_chunks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, content, chunk_type FROM chunks;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def extract_concepts(chunks):
    combined = "\n\n".join([f"[{ctype}] {content}" for _, content, ctype in chunks])
    
    response = client.chat.completions.create(
        model="llama3.2:latest",
        messages=[
            {
                "role": "system",
                "content": """You are an expert at analyzing study material. 
Extract the key concepts from the provided notes and problems.
Return ONLY a JSON object in this exact format, nothing else:
{
  "concepts": ["concept 1", "concept 2", ...],
  "combinations_seen": [["concept A", "concept B"], ...],
  "combinations_unseen": [["concept X", "concept Y"], ...]
}
combinations_seen = concept pairs that appear together in problems.
combinations_unseen = concept pairs from notes that haven't been combined in problems yet.
These unseen combinations are the gaps we want to generate problems for."""
            },
            {
                "role": "user",
                "content": f"Analyze this study material:\n\n{combined}"
            }
        ]
    )
    
    raw = response.choices[0].message.content
    start = raw.find('{')
    end = raw.rfind('}') + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in response: {raw}")
    return json.loads(raw[start:end])

def save_concepts(concepts_data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS concepts (
            id SERIAL PRIMARY KEY,
            data JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cur.execute("INSERT INTO concepts (data) VALUES (%s)", [json.dumps(concepts_data)])
    conn.commit()
    cur.close()
    conn.close()
    print("Concepts saved.")

if __name__ == "__main__":
    print("Fetching chunks...")
    chunks = get_all_chunks()
    print(f"Analyzing {len(chunks)} chunks...")
    concepts = extract_concepts(chunks)
    print("\nConcepts found:")
    print(json.dumps(concepts, indent=2))
    save_concepts(concepts)