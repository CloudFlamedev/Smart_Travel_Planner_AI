# Smart Travel Planner

An intentionally small, AI-powered travel-planning project for learning FastAPI, React + TypeScript, REST APIs, Docker, and local full-stack development.

It accepts a trip’s origin, destination, duration, travellers, budget, and interests, then uses Groq to create a structured itinerary. Transport pricing is always presented as an approximate estimate; it is not live pricing or booking availability.

## Architecture

```text
React + Vite (localhost:5173)
          │ POST /api/trips/plan
          ▼
FastAPI (localhost:8000) ──► Groq Chat Completions API
          │                         │
          └── validates JSON ◄──────┘
```

No database is required in this first version. Trips are generated on demand and are not stored.

## Technology

- Frontend: React, TypeScript, Vite, Tailwind CSS, Axios, Lucide icons
- Backend: Python, FastAPI, Pydantic, httpx, Uvicorn
- AI: Groq’s OpenAI-compatible chat-completions API with JSON-schema structured output
- Local containers: Docker and Docker Compose

## Folder structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/trip.py          # trip endpoint
│   │   ├── core/config.py       # environment settings
│   │   ├── schemas/trip.py      # Pydantic request / response models
│   │   ├── services/groq_service.py
│   │   └── main.py
│   ├── tests/test_api.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/components/
│   ├── src/api.ts
│   ├── src/types.ts
│   └── Dockerfile
├── .env.example
└── docker-compose.yml
```

## Environment variables

Create the local file before running the app:

```bash
cp .env.example .env
```

Then add your Groq key:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
FRONTEND_ORIGIN=http://localhost:5173
```

`GROQ_API_KEY` is read only by FastAPI. Never add it to a `VITE_*` variable or expose it in frontend code. `.env` is ignored by Git.

## Run locally

Requirements: Python 3.11+ and Node.js 20+.

In one terminal, start the API:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In a second terminal, start the frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`. The provided frontend environment points to `http://localhost:8000` by default.

## API

### Health check

`GET /health`

```json
{"status":"healthy"}
```

### Generate a plan

`POST /api/trips/plan`

```json
{
  "source": "Bangalore",
  "destination": "Delhi",
  "duration": 4,
  "travelers": 2,
  "budget": 20000,
  "interests": ["history", "food", "culture"]
}
```

The response contains the submitted trip facts, a list of places, approximate transport options, one itinerary entry per day, and four to six travel tips. Invalid input returns FastAPI’s standard `422` response. Missing configuration, Groq failures, timeouts, and malformed model output return clear `5xx` errors without returning fabricated travel data.

Interactive API documentation is available at `http://localhost:8000/docs` while the backend is running.

## Groq integration

The backend calls Groq directly with `httpx`. It sends a system instruction that prohibits claims of live prices or availability, asks for JSON matching the `TripPlan` schema, and validates the returned JSON with Pydantic before returning it to the browser. This keeps the frontend simple and keeps the secret key on the server.

The default model supports Groq’s JSON-schema structured-output format. If you choose another model, confirm it supports structured outputs.

## Tests

Tests never call Groq. They substitute a small in-memory service for the endpoint test.

```bash
cd backend
source .venv/bin/activate
pytest
```

## Docker local setup

After creating root `.env` as above:

```bash
docker compose up --build
```

The frontend is served at `http://localhost:5173` and the API at `http://localhost:8000`. Stop the stack with `docker compose down`.

This repository deliberately contains no AWS, Terraform, Kubernetes, Jenkins, booking, authentication, or database setup.
