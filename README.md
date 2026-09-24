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

CloudOps AI solves a real problem: companies using AWS often have no clear visibility into their cloud spend, no way to predict next month's bill, and no easy way to ask "why did our costs go up?" without manually digging through dashboards.

This platform provides:
- Secure, multi-tenant cost tracking - connect an AWS account, see real cost data, isolated per organization
- Role-based access control - Admin, Manager, and Viewer roles, enforced on both backend and frontend
- ML-based cost forecasting - predicts next 30 days of spend, with honest, validated accuracy metrics
- A multi-agent GenAI Copilot - ask questions in plain English, get answers grounded in real cost and forecast data, with an automated verification step checking every cited number

## Tech Stack

**Backend:** Python, Django, Django REST Framework, PostgreSQL + pgvector, Redis, Celery, JWT auth

**AI / ML:** scikit-learn, pandas, numpy, Google Gemini API, custom multi-agent RAG pipeline

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
- Validated with MAE, typically -16 per day against average daily spend of -150
- Forecasts saved to a history table for future predicted-vs-actual comparison

## GenAI Copilot: A Real Multi-Agent Pipeline

Rather than a single LLM call, the Copilot is built as three cooperating agents:

1. **Router** - a small, focused LLM call that decides what data the question actually needs (historical spend, forecast, or both) before anything else happens
2. **Analyst** - drafts a natural-language answer using only the data the Router said was needed
3. **Verifier** - a deterministic, non-LLM check that extracts every number the Analyst cited and confirms it genuinely appears in the real source data, flagging the answer if it doesn't

This was tested against 12 varied questions, including:
- Direct questions it can answer ("what's our total cost?", "which service costs the most?") - answered accurately, with correct figures
- Forward-looking questions ("what will we spend next month?") - correctly pulls and cites the ML forecast, including its error margin
- Causal questions the data can't explain ("why did costs increase?") - correctly declines to speculate
- Out-of-range questions ("what did we spend in 2020?") - correctly states the data doesn't cover that period
- Judgment-based questions ("should I switch from EC2 to Lambda?") - cites the real relevant numbers but correctly declines to make a recommendation the data can't support
- Completely unrelated questions ("what's the weather today?") - correctly declines, no data fabricated

Building the Verifier surfaced real, subtle challenges worth noting: distinguishing cost figures from incidental numbers like day-counts, calendar years, and digits embedded in service names (the "3" in "S3", the "2" in "EC2") required iterative refinement - a genuine lesson in the gap between "looks correct" and "is provably correct."

## Project Phases

1. Foundation - Custom User model, JWT auth, multi-tenant Organizations, RBAC
2. Cloud Integration - Real AWS Cost Explorer integration via boto3, async Celery ingestion, later upgraded to STS AssumeRole
3. Analytics - Aggregate cost queries, Redis-cached summaries, CSV export
4. ML Forecasting - Feature engineering, chronological validation, 30-day predictions
5. GenAI Copilot - Multi-agent pipeline (Router, Analyst, Verifier), grounded in real data, hallucination-tested
6. Production Deployment - Docker, AWS EC2, Nginx, HTTPS, CI/CD, full-stack React frontend

## Local Setup

\\\
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
\\\

## Running Tests

\\\
python manage.py test
\\\

17 automated tests covering authentication, RBAC, multi-tenant isolation, analytics correctness, ML forecasting (including edge cases), and Copilot behavior. Runs automatically on every push via GitHub Actions.

## What I Would Add With More Time

- Anomaly detection on cost/usage spikes
- Idle resource detection for cost savings
- Multi-cloud support (GCP, Azure)
- A managed database (RDS) instead of a self-hosted Postgres container
- Streaming Copilot responses instead of waiting for the full answer
- Conversation memory so the Copilot can handle multi-turn follow-up questions

## Author

**Mohamed Ashik**
[GitHub](https://github.com/mohamedashik110)
