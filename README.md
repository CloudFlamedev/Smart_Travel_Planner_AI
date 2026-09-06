<div align="center">

# ✈️ Smart Travel Planner AI

**An AI-powered trip planning app that turns a few inputs — origin, destination, duration, budget — into a fully structured, personalized itinerary in seconds.**

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://smart-travel-planner-ai-five.vercel.app)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](#-running-with-docker)
[![CI](https://img.shields.io/badge/CI-Jenkins-D24939?logo=jenkins&logoColor=white)](#-cicd)
[![IaC](https://img.shields.io/badge/IaC-Terraform%20%2B%20Kubernetes-844FBA?logo=terraform&logoColor=white)](#-cloud-deployment-aws)
[![License](https://img.shields.io/badge/license-MIT-blue)](#-license)

[Live Demo](https://smart-travel-planner-ai-five.vercel.app) · [Report an Issue](../../issues)

</div>

---

## 📖 Overview

Smart Travel Planner AI is a full-stack web application that generates a custom travel itinerary using a large language model. A user fills in a short form — **From, To, Duration, Travelers, Budget,** and optional **Interests** — and the backend calls an LLM (via Groq) to produce a structured plan: places to visit, a getting-there breakdown, and practical AI-generated travel notes, all rendered as a clean, card-based UI.

The project was built to be **cloud-portable by design**: the same Docker images run identically on a local machine, on Vercel (current live deployment), or on AWS EKS via the included Terraform + Kubernetes configuration — with one CI/CD pipeline (Jenkins) driving builds and tests across all of it.

## 🌐 Live Demo

**[smart-travel-planner-ai-five.vercel.app](https://smart-travel-planner-ai-five.vercel.app)**

Try it with something like: *From: Delhi → To: Kashmir, 4 days, 2 travelers, ₹20,000 budget.*

## ✨ Features

- **AI-generated itineraries** — natural-language trip requirements turned into structured JSON (places, categories, descriptions) by an LLM, not a static template.
- **Categorized places to visit** — each recommendation tagged (Nature, Cultural, Adventure, Scenic Spot, etc.) with a short description.
- **AI travel notes** — practical, trip-specific tips (packing, cash/connectivity, local customs, safety) generated alongside the itinerary.
- **Getting-there guidance** — transport context between origin and destination.
- **Budget- and traveler-aware planning** — the model factors in party size and budget when shaping recommendations.
- **Responsive, modern UI** — card-based layout built with React, TypeScript, and Tailwind CSS.
- **Graceful failure handling** — clear, user-facing error states instead of silent failures or raw stack traces.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React, TypeScript, Vite, Tailwind CSS, Axios |
| **Backend** | Python, FastAPI, Pydantic |
| **AI / LLM** | Groq API (`openai/gpt-oss-20b`) |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | Jenkins (test → build → containerize pipeline) |
| **Hosting (current)** | Vercel (serverless functions + static frontend) |
| **Infrastructure as Code** | Terraform (VPC, ECR, EKS) |
| **Orchestration** | Kubernetes (Deployments, Services, Ingress, HPA) — AWS EKS-ready |

## 🏗️ Architecture

```
┌─────────────────┐        HTTPS         ┌──────────────────────┐
│   React + Vite    │ ───────────────────▶ │   FastAPI Backend    │
│   (frontend)       │  POST /api/trips/plan │   (backend)           │
│   Tailwind UI       │ ◀─────────────────── │   Pydantic schemas    │
└─────────────────┘      JSON itinerary    └───────────┬──────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────────┐
                                                 │   Groq LLM API    │
                                                 │ openai/gpt-oss-20b │
                                                 └──────────────────┘
```

Both services are independently Dockerized and communicate over a defined API contract (`/api/trips/plan`), which keeps the frontend and backend deployable together *or* separately — the same layout works whether they're two containers in Docker Compose, two Kubernetes Deployments behind one Ingress, or a static frontend + serverless function on Vercel.

## 📁 Project Structure

```
Smart_Travel_Planner/
├── frontend/                 # React + TypeScript + Vite app
│   ├── src/
│   │   ├── api.ts             # Axios client, same-origin by default
│   │   ├── App.tsx
│   │   ├── types.ts
│   │   └── components/
│   ├── Dockerfile
│   └── package.json
├── backend/                  # FastAPI service
│   ├── app/
│   │   ├── main.py             # FastAPI app, routes, health check
│   │   ├── core/                # config, settings
│   │   ├── schemas/               # Pydantic request/response models
│   │   └── services/               # Groq LLM integration
│   ├── requirements.txt
│   └── Dockerfile
├── api/                       # Vercel serverless entrypoint
│   └── index.py
├── infra/                     # AWS-ready Infrastructure as Code
│   ├── terraform/                # VPC, ECR, EKS cluster
│   └── k8s/                       # Deployments, Services, Ingress, HPA
├── docker-compose.yml         # Local multi-container dev environment
├── vercel.json                # Vercel build + routing config
├── Jenkinsfile                # CI pipeline definition
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) & Docker Compose
- A [Groq API key](https://console.groq.com/) (free tier available)
- Node.js 18+ and Python 3.12+ (only needed for running outside Docker)

### Run with Docker (recommended)

```bash
git clone https://github.com/CloudFlamedev/Smart_Travel_Planner_AI.git
cd Smart_Travel_Planner_AI

# Create a .env file at the project root
echo "GROQ_API_KEY=your_key_here" > .env

docker-compose up --build
```

- Frontend → [http://localhost:5173](http://localhost:5173)
- Backend API → [http://localhost:8000](http://localhost:8000)
- Health check → [http://localhost:8000/health](http://localhost:8000/health)

### Run without Docker

**Backend:**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🔑 Environment Variables

| Variable | Where | Description |
|---|---|---|
| `GROQ_API_KEY` | Backend | API key for the Groq LLM service |
| `GROQ_MODEL` | Backend | Model identifier (default: `openai/gpt-oss-20b`) |
| `FRONTEND_ORIGIN` | Backend | Allowed CORS origin for the frontend |
| `VITE_API_URL` | Frontend (build-time) | Base API URL; left empty for same-origin deployments (Vercel/K8s), set for local dev pointing at a separate backend host |

## 📡 API Reference

**`POST /api/trips/plan`**

Request body:
```json
{
  "origin": "Delhi",
  "destination": "Kashmir",
  "duration_days": 4,
  "travelers": 2,
  "budget": 20000,
  "interests": "history, food, culture"
}
```

Response: a structured itinerary — destination summary, categorized places to visit, transport notes, and AI-generated travel tips.

**`GET /api/health`** — liveness/readiness check, returns `{"status": "healthy"}`.

## ⚙️ CI/CD

The Jenkins pipeline (`Jenkinsfile`) runs on every push:

1. **Checkout** — pull latest source
2. **Backend Tests** — spin up a virtualenv, install dependencies, run `pytest`
3. **Frontend Build** — `npm ci && npm run build`, catching build-time errors early
4. **Docker Build** — build both service images via Compose, validating the containers are production-buildable before merge

## ☁️ Deployment

This project is deliberately built to run identically across environments:

- **Current live deployment:** [Vercel](https://vercel.com) — static frontend + FastAPI served as a serverless function, config in `vercel.json`.
- **AWS-ready:** `infra/terraform/` provisions a VPC, ECR repositories, and an EKS cluster; `infra/k8s/` contains production-style Deployments, Services, an ALB Ingress, and a HorizontalPodAutoscaler for the backend — see [`infra/README.md`](infra/README.md) for the full walkthrough from `terraform apply` to `kubectl apply`.

Both deployment paths run from the **same Docker images**, so moving between them is a config change, not a rewrite.

## 🗺️ Roadmap

- [ ] Persist generated itineraries (database-backed trip history)
- [ ] User accounts and saved trips
- [ ] Multi-city / multi-leg itinerary support
- [ ] Automated `kubectl apply` stage in the Jenkins pipeline
- [ ] Unit test coverage for the frontend (Vitest)

## 🤝 Contributing

Issues and pull requests are welcome. For significant changes, please open an issue first to discuss what you'd like to change.

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

## 👤 Author

**Utkrist**
Systems Engineer, TCS · Bengaluru, India
GitHub: [@CloudFlamedev](https://github.com/CloudFlamedev)

---

<div align="center">
Built as an end-to-end exercise in shipping a full-stack AI product — from LLM integration and containerization to CI/CD and cloud-portable infrastructure.
</div>
