import os
import sys
from pypdf import PdfReader
from db import get_chunks_collection, get_concepts_collection
from dotenv import load_dotenv

load_dotenv()

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
    print(f"Created {len(chunks)} chunks, storing...")

    collection = get_chunks_collection()
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            metadatas=[{"source": filepath, "chunk_type": chunk_type}],
            ids=[f"{filepath}_{i}"]
        )
    print(f"Done! {len(chunks)} chunks stored.")

if __name__ == "__main__":
    ingest_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "notes")