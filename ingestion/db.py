import chromadb
import os

client = chromadb.PersistentClient(path=os.path.expanduser("~/Documents/synthesis/data"))

def get_chunks_collection():
    return client.get_or_create_collection("chunks")

def get_concepts_collection():
    return client.get_or_create_collection("concepts")

def get_problems_collection():
    return client.get_or_create_collection("problems")