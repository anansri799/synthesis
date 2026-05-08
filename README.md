---
title: Synthesis
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Synthesis
### Adaptive problem generator for students with testing anxiety
 
Most study tools pull questions from a bank. Synthesis generates novel problems by reasoning about the gaps in your knowledge — concepts you understand individually but have never been tested on together. It also learns the difference between a genuine knowledge gap and anxiety-driven freeze, and adapts accordingly.
 
---
 
## How it works
 
1. **Upload your notes and past problem sets** — lecture PDFs, homework, anything
2. **Synthesis extracts concepts** and maps which combinations have and haven't appeared in problems you've seen
3. **A novel problem is generated** targeting an untested concept combination
4. **Unlock hints progressively** — three levels, each one giving a little more away. You choose when you need help
5. **Submit your answer** — an LLM grades it, gives a score, specific feedback, and tells you what you missed
---
 
## Stack
 
| Layer | Tool |
|-------|------|
| Vector database | ChromaDB |
| LLM inference | Ollama (local) → NVIDIA NIM (production) |
| Model optimization | TensorRT-LLM |
| API | FastAPI |
| Frontend | React + Vite |
| Deployment | Kubernetes + Helm + NVIDIA GPU Operator |
 
The inference layer is OpenAI-compatible — swapping from local Ollama to NVIDIA NIM is a one-line change in `.env`. This was an intentional architectural decision: latency matters in a study tool. A 3-second spinner after a wrong answer breaks focus. NIM keeps hint generation under 200ms.
 
---
 
## Running locally
 
**Prerequisites:** Python 3.11+, Node.js, Docker, Ollama
 
```bash
# Clone and set up
git clone https://github.com/yourusername/synthesis
cd synthesis
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
 
# Start the vector database
docker run -d --name synthesis-db \
  -e POSTGRES_PASSWORD=synthesis \
  -p 5432:5432 ankane/pgvector
 
# Set environment variables
cp .env.example .env
# Add your API key to .env
 
# Pull a model
ollama pull llama3.2
 
# Start the backend
uvicorn api.main:app --port 8000
 
# Start the frontend
cd frontend && npm install && npm run dev
```
 
Open `http://localhost:5173`
 
---
 
## API endpoints
 
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest` | Upload a PDF (notes or past problems) |
| POST | `/generate` | Generate a novel problem |
| GET | `/hint/{problem_id}/{n}` | Unlock hint 1, 2, or 3 |
| POST | `/submit/{problem_id}` | Submit answer, get graded feedback |
 
---
 
## Roadmap
 
- **Anxiety fingerprinting** — track time-per-problem and hint unlock speed to distinguish knowledge gaps from anxiety freeze
- **Simulated test environment** — progressively timed sessions that desensitize you to exam pressure
- **Past exam pattern matching** — upload previous tests to generate problems that match your professor's style and weighting
- **NVIDIA NIM deployment** — GPU-accelerated inference for production
- **LoRA fine-tuning** — fine-tune hint generation behavior so hints guide without giving away answers
---
 
## Why this exists
 
Testing anxiety affects a lot of students. The problem usually isn't that they don't know the material but rather that there is blank-page panic under pressure makes them forget what they know. Existing tools either throw more flashcards at you or simulate tests without any support structure.
 
Synthesis tries to do something different: generate problems at the exact edge of your knowledge, give you a safety net you control, and over time help you build confidence under pressure.
