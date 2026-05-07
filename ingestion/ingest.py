import os
import sys
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from db import get_connection
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def ingest_pdf(filepath, chunk_type="notes"):
    print(f"Reading {filepath}...")
    reader = PdfReader(filepath)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + " "

    chunks = chunk_text(full_text)
    print(f"Created {len(chunks)} chunks, embedding...")

    embeddings = model.encode(chunks)

    conn = get_connection()
    cur = conn.cursor()
    for chunk, embedding in zip(chunks, embeddings):
        cur.execute(
            "INSERT INTO chunks (content, source, chunk_type, embedding) VALUES (%s, %s, %s, %s)",
            (chunk, filepath, chunk_type, embedding.tolist())
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Done! {len(chunks)} chunks stored.")

if __name__ == "__main__":
    ingest_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "notes")