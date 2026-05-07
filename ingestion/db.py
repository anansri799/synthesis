import os
from psycopg2 import connect
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return connect(os.getenv("DATABASE_URL"))

def setup_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id SERIAL PRIMARY KEY,
            content TEXT,
            source TEXT,
            chunk_type TEXT,
            embedding vector(384)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Database ready.")

if __name__ == "__main__":
    setup_db()