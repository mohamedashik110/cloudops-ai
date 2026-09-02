# CloudOps AI - Enterprise Cloud Intelligence Platform

A full-stack, production-deployed SaaS platform that helps organizations monitor cloud costs, forecast future spending with machine learning, and get grounded AI-powered answers about their cloud spend - built end-to-end with Django, React, real AWS integration, and Google Gemini.

**Live demo:** https://cloudops-ai.duckdns.org
**Repository:** https://github.com/mohamedashik110/cloudops-ai

## Try it yourself
URL: https://cloudops-ai.duckdns.org
Username: demo
Password: mohamed0902

This is a read-only (Viewer) demo account - safe to explore. All data belongs to a demo organization seeded with 90 days of realistic synthetic cost data.

---

## What This Project Does

CloudOps AI solves a real problem: companies using AWS often have no clear visibility into their cloud spend, no way to predict next month bill, and no easy way to ask "why did our costs go up?" without manually digging through dashboards.

This platform provides:
- Secure, multi-tenant cost tracking - connect an AWS account, see real cost data, isolated per organization
- Role-based access control - Admin, Manager, and Viewer roles with different permissions, enforced on both backend and frontend
- ML-based cost forecasting - predicts next 30 days of spend, with honest, validated accuracy metrics
- A GenAI Copilot - ask questions in plain English, get answers grounded in real cost data, with citations

## Tech Stack

**Backend:** Python, Django, Django REST Framework, PostgreSQL + pgvector, Redis, Celery, JWT auth

**AI / ML:** scikit-learn, pandas, numpy, Google Gemini API, custom RAG-style grounding

**Frontend:** React (Vite), React Router, Axios, Recharts, Lucide React

**Infrastructure:** Docker, Docker Compose, AWS EC2, IAM, STS, Nginx, Let's Encrypt, GitHub Actions CI

## Security Highlights

- No permanent AWS credentials stored. Customers create a scoped IAM Role and grant CloudOps AI permission to assume it via AWS STS, using a unique External ID to prevent the confused deputy problem. Temporary credentials auto-expire in one hour.
- Role-based access control enforced identically on backend and frontend.
- Multi-tenant data isolation, verified with automated tests.
- HTTPS everywhere via a free Let's Encrypt certificate with auto-renewal.

## Machine Learning: Cost Forecasting

- Features: 7-day rolling average, day-of-week seasonality, trend index
- Chronological train/test split (not random) - avoids data leakage
- Validated with MAE, typically $11-16 per day against average daily spend of $60-150
- Forecasts saved to a history table for future predicted-vs-actual comparison

## GenAI Copilot: Grounded, Not Guessing

The Copilot retrieves real cost data before generating any answer, and is explicitly instructed to say "I do not have that information" rather than fabricate numbers. Tested against real, causal, and out-of-range questions - it only ever cites real numbers or admits it does not know.

## Project Phases

1. Foundation - Custom User model, JWT auth, multi-tenant Organizations, RBAC
2. Cloud Integration - Real AWS Cost Explorer integration via boto3, async Celery ingestion, later upgraded to STS AssumeRole
3. Analytics - Aggregate cost queries, Redis-cached summaries, CSV export
4. ML Forecasting - Feature engineering, chronological validation, 30-day predictions
5. GenAI Copilot - Gemini-powered chat, grounded in real data, hallucination-tested
6. Production Deployment - Docker, AWS EC2, Nginx, HTTPS, CI/CD, full-stack React frontend

## Local Setup
git clone https://github.com/mohamedashik110/cloudops-ai.git
cd cloudops-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d
python manage.py migrate
python manage.py runserver 8080

cd frontend
npm install
npm run dev

## Running Tests

17 automated tests covering authentication, RBAC, multi-tenant isolation, analytics correctness, ML forecasting, and Copilot behavior. Runs automatically on every push via GitHub Actions.

## What I Would Add With More Time

- Anomaly detection on cost/usage spikes
- Idle resource detection for cost savings
- Multi-cloud support (GCP, Azure)
- Managed database (RDS)
- Connect the Copilot to ML forecast data for forward-looking questions

## Author

**Mohamed Ashik**
[GitHub](https://github.com/mohamedashik110)
