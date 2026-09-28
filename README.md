# CloudOps AI - Enterprise Cloud Intelligence Platform

A full-stack, production-deployed platform that helps organizations understand their cloud spending, forecast future costs with machine learning, and ask questions about their bill in plain English through a grounded, multi-agent AI Copilot.

| | |
|---|---|
| Live app | https://cloudops-ai.duckdns.org |
| Source code | https://github.com/mohamedashik110/cloudops-ai |
| Author | Mohamed Ashik |

## Try it yourself

    URL:      https://cloudops-ai.duckdns.org
    Username: demo
    Password: mohamed0902

This is a read-only Viewer account inside a demo organization. It is safe to explore: you can view the dashboard, cost records, cloud accounts and use the AI Copilot, but you cannot connect new cloud accounts. The demo data is synthetic (90 days of generated cost data, flagged `is_synthetic` in the database) and is clearly labelled "Demo" in the UI.

Suggested things to try in the Copilot:

- "What is our total cost?"
- "Which service costs the most?"
- "What will we spend next month?"
- "Why did our costs increase?" (it should refuse to guess)
- "What did we spend in 2020?" (it should say it has no data for that)

---

## Table of contents

1. Why I built this
2. The problem it solves
3. Features
4. Architecture
5. Tech stack
6. Roles and permissions
7. Security design
8. Machine learning: cost forecasting
9. AI Copilot: a multi-agent pipeline
10. API reference
11. Frontend pages
12. Deployment and CI/CD
13. Connecting a real AWS account (IAM setup guide)
14. Local setup
15. Testing
16. Project structure
17. Engineering challenges and what I learned
18. Known limitations
19. Roadmap

---

## 1. Why I built this

I wanted to build something that looks like the software real product companies actually ship, not a tutorial clone. Most fresher portfolio projects are a CRUD app with a single chatbot bolted on, running only on localhost. I set myself a harder bar:

- A real backend problem with real security constraints, not just forms and tables
- A real integration with an external system (AWS), not mocked data only
- Machine learning that is validated honestly, not a model with a made-up accuracy number
- A GenAI feature that is provably grounded in data and admits when it does not know
- Something that is genuinely deployed with HTTPS, a domain, CI, and tests, so anyone can open it and use it

Cloud cost management was a good fit because it forces all of these together: multi-tenant data, sensitive credentials, time-series data, and a natural use case for natural-language questions.

## 2. The problem it solves

Almost every company running on AWS eventually hits the same set of problems:

| Problem | How CloudOps AI addresses it |
|---|---|
| Nobody can easily see where the cloud bill is going | Dashboard with total spend, daily trend and per-service breakdown |
| The bill is a surprise at the end of the month | ML forecast of the next 30 days, with its typical error shown honestly |
| Getting answers means digging through consoles and spreadsheets | AI Copilot answers questions in plain English using the company's real numbers |
| AI chatbots make up numbers | Grounded retrieval plus an automated Verifier that checks every number the AI cites |
| Third-party tools ask you to hand over permanent AWS keys | The platform never stores customer credentials; it uses short-lived STS credentials via a scoped IAM role |
| Different people need different access | Admin / Manager / Viewer roles enforced on both API and UI |
| Multiple teams or companies on one platform must not see each other's data | Multi-tenant isolation at the query level, covered by automated tests |

## 3. Features

- Secure multi-tenant accounts: registering creates an organization, and the first user becomes its Admin
- JWT authentication with access and refresh tokens
- Role-based access control (Admin, Manager, Viewer)
- Cloud account connection using an IAM Role ARN and External ID (no stored AWS secrets)
- Asynchronous cost ingestion from AWS Cost Explorer using Celery and Redis, with retry logic
- Cost analytics: totals, top services, daily trends, cached in Redis
- CSV cost report export
- ML cost forecasting with saved forecast history
- Multi-agent AI Copilot (Router, Analyst, Verifier) with cited sources
- React frontend with protected routes and role-aware UI
- Health-check endpoint, production logging, non-root containers
- Automated test suite running on every push through GitHub Actions

## 4. Architecture

Everything runs on one AWS EC2 instance (Ubuntu, t3.small) as Docker containers, with Nginx in front serving both the frontend and the API on a single HTTPS domain.

                         Internet (HTTPS, port 443)
                                    |
                            +---------------+
                            |     Nginx     |   TLS via Let's Encrypt
                            +---------------+
                             |             |
              static files   |             |   /api/ and /admin/
                             v             v
                  +----------------+   +------------------------+
                  | React frontend |   | Django REST API        |
                  | (Vite build)   |   | (Gunicorn, container)  |
                  +----------------+   +------------------------+
                                          |        |         |
                          +---------------+        |         +---------------+
                          v                        v                         v
                  +---------------+        +--------------+          +---------------+
                  | PostgreSQL 16 |        |    Redis     |<---------|    Celery     |
                  | + pgvector    |        | cache/broker |          |    worker     |
                  +---------------+        +--------------+          +---------------+
                                                                             |
                                          +----------------------------------+
                                          v
                        +-------------------------------+      +--------------------+
                        | AWS STS AssumeRole            |      | Google Gemini API  |
                        |   -> Cost Explorer (customer) |      | (Router, Analyst)  |
                        +-------------------------------+      +--------------------+

Request flow for a Copilot question: browser -> Nginx -> Django (JWT checked, organization resolved) -> Router agent -> data retrieval (cost summary and/or ML forecast) -> Analyst agent -> Verifier -> response with sources.

Because the frontend and API share one domain through Nginx, the production frontend calls a relative `/api/v1` path, which avoids CORS entirely in production.

## 5. Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | PostgreSQL 16 with the pgvector extension |
| Cache and queue | Redis |
| Background jobs | Celery |
| ML | scikit-learn, pandas, numpy |
| GenAI | Google Gemini API, custom multi-agent pipeline |
| Cloud integration | boto3, AWS STS, AWS Cost Explorer |
| Frontend | React (Vite), React Router, Axios, Recharts, Lucide icons |
| Web server | Nginx (reverse proxy and static hosting) |
| TLS | Let's Encrypt via Certbot, DuckDNS domain |
| Containers | Docker, Docker Compose |
| Hosting | AWS EC2 |
| CI | GitHub Actions |

## 6. Roles and permissions

| Capability | Viewer | Manager | Admin |
|---|---|---|---|
| View dashboard, cost records, cloud accounts | Yes | Yes | Yes |
| Use the AI Copilot | Yes | Yes | Yes |
| View forecasts | Yes | Yes | Yes |
| Connect a new cloud account | No | Yes | Yes |
| List all users in the organization | No | No | Yes |

These rules are enforced in the API using Django REST Framework permission classes. The UI mirrors them (a Viewer simply does not see the "Connect Account" button), but the UI is only a convenience: the backend is what actually enforces access, and returns 403 if a Viewer tries anyway.

## 7. Security design

**No stored customer credentials.** Early in the project, the CloudAccount model stored AWS access keys. I recognized that this is a serious risk: a database breach would expose long-lived credentials for every customer. I redesigned it to the pattern used by real SaaS vendors:

1. The customer creates an IAM Role in their own AWS account with a narrow read-only policy for Cost Explorer.
2. The role's trust policy allows CloudOps AI to assume it, but only when a unique External ID is presented.
3. The customer gives CloudOps AI only the Role ARN. The External ID is generated by the platform.
4. When syncing, the backend calls STS AssumeRole and receives temporary credentials that expire after about one hour.

The External ID protects against the "confused deputy" problem, where a third party could trick the platform into accessing someone else's role.

**Tenant isolation.** Every query is scoped to the requesting user's organization. Automated tests verify that a user in one organization sees zero data from another.

**Other measures:** HTTPS with auto-renewing certificates, secrets only in environment variables (never committed), `DEBUG=False` in production, containers running as a non-root user, JWT access tokens that expire after one hour, and a `.gitignore` that excludes `.env`.

## 8. Machine learning: cost forecasting

The goal is to predict the next 30 days of spend from the organization's cost history.

**Features** (built in `ml_engine/services.py`):

- 7-day rolling average, to smooth daily noise
- Day of week, to capture weekly patterns (costs dip on weekends)
- A trend index, to capture gradual growth

**Model:** Linear Regression from scikit-learn. I deliberately chose a simple model I can fully explain over a complex one I cannot defend.

**Validation:** a chronological split. The model trains on the oldest days and is tested on the most recent days, so it never sees "the future" during training (avoiding data leakage). Random splitting would be wrong for time series. The reported metric is Mean Absolute Error (MAE), which was typically about 11 to 16 USD per day against average daily spend of roughly 60 to 150 USD on the demo data.

**Forecast:** the model is retrained on all available history and predicts forward. Future rolling averages are not knowable, so the last known value is held constant. This is a stated simplification.

**Edge cases:** if an organization has too little history, the API returns a clear 400 error instead of a bad prediction (covered by a test). Every forecast is saved to a history table so predicted-versus-actual comparison is possible later.

## 9. AI Copilot: a multi-agent pipeline

A single "stuff everything into one prompt" call is easy to build and hard to trust. The Copilot instead separates planning, retrieval, drafting and verification:

    Question
       |
       v
    [Agent 1: Router]      Small LLM call. Decides what data is needed:
       |                   historical spend, forecast, or both.
       v
    [Retrieval]            Plain Python, not an LLM. Fetches only the data
       |                   the Router asked for (cost summary / ML forecast).
       v
    [Agent 2: Analyst]     LLM call. Drafts an answer using ONLY that data
       |                   and is told to say so if the data cannot answer.
       v
    [Agent 3: Verifier]    Deterministic Python. Extracts every number in
       |                   the draft and checks it against the real data.
       v
    Answer + sources + verified flag + the Router's plan

**Why a Verifier that is not an LLM:** using another model to check the first one just moves the hallucination risk. A deterministic check that says "this number does not appear in the data I retrieved" is simple, explainable, and cannot itself hallucinate.

### What the Copilot can and cannot answer

| Type of question | Example | Behaviour |
|---|---|---|
| Historical totals | "What is our total cost?" | Answers with the real figure |
| Service breakdown | "Which service costs the most?" | Answers with real per-service amounts |
| Forecast | "What will we spend next month?" | Cites the ML forecast and its average error |
| Causal | "Why did our costs increase?" | Declines to speculate; the data has no cause information |
| Out of range | "What did we spend in 2020?" | States that the data does not cover that period |
| Judgment | "Should I switch from EC2 to Lambda?" | Cites the relevant real costs but declines to make a recommendation the data cannot support |
| Unrelated | "What is the weather today?" | Declines; no data is invented |
| Vague | "Tell me stuff" | Gives a summary of the data it has |

I tested a set of 12 questions like these against the live deployment. Every answer was substantively correct or an honest refusal.

### Verifier design notes

The Verifier ignores numbers that are legitimate but are not cost figures: day counts ("30 days", "90 days of history"), calendar years, and digits inside service names (the 3 in S3, the 2 in EC2). It normalizes formatting such as thousands separators and allows tiny rounding differences. Getting this right took several iterations. It is a heuristic, and it can occasionally flag a correct answer as "please double-check" when the model paraphrases a figure. I chose to accept that: being occasionally over-cautious is a better failure mode than ever missing a real fabricated number.

## 10. API reference

Base path: `/api/v1`. All endpoints except register and login require `Authorization: Bearer <access token>`.

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| POST | /auth/register/ | Create a user and organization | Public |
| POST | /auth/login/ | Obtain access and refresh tokens | Public |
| POST | /auth/login/refresh/ | Refresh an access token | Public |
| GET | /auth/me/ | Current user profile and role | Authenticated |
| GET | /auth/org-users/ | List users in the organization | Admin |
| GET | /cloud-accounts/ | List connected cloud accounts | Authenticated |
| POST | /cloud-accounts/ | Connect a cloud account (Role ARN) | Manager, Admin |
| GET | /cost-records/ | List cost records (optional service filter) | Authenticated |
| GET | /analytics/summary/?days=90 | Total, top services, daily trend | Authenticated |
| GET | /reports/monthly/?days=90 | Download a CSV cost report | Authenticated |
| GET | /predictions/forecast/?days=30 | Generate and save a forecast | Authenticated |
| GET | /predictions/history/ | Previous forecasts | Authenticated |
| POST | /copilot/chat/ | Ask the AI Copilot a question | Authenticated |
| GET | /health/ (outside /api/v1) | Liveness check | Public |

## 11. Frontend pages

- **Login:** authenticates against the JWT endpoint and stores tokens; redirects to the dashboard.
- **Dashboard:** summary cards (total cost, predicted next 30 days, forecast MAE), a daily cost trend line chart, and a cost-by-service pie chart. The forecast loads independently, so a forecast failure does not break the rest of the page.
- **Cloud Accounts:** table of connected accounts; the "Connect Account" form is shown only to Managers and Admins.
- **Cost Records:** filterable table of raw cost line items, with a Demo/Real badge.
- **AI Copilot:** chat interface with the answer, and the source figures shown under each response.

Frontend design points: a central Axios instance attaches the JWT to every request and redirects to login on a 401; an AuthContext holds the logged-in user globally; a ProtectedRoute component guards private pages.

## 12. Deployment and CI/CD

**Production stack.** Docker Compose runs four containers on a single EC2 instance: PostgreSQL (with pgvector), Redis, the Django app under Gunicorn, and a Celery worker. Nginx runs on the host, serving the built React app from `/var/www` and proxying `/api/` and `/admin/` to Django. TLS certificates come from Let's Encrypt and renew automatically. An Elastic IP keeps the address stable, and a free DuckDNS domain points to it.

**Continuous integration.** A GitHub Actions workflow runs the full test suite on every push and pull request, against real Postgres and Redis service containers.

**Deploying a change** (manual, currently):

    ssh into the server
    cd ~/cloudops-ai
    git pull
    docker compose exec web python manage.py migrate
    docker compose up -d --build

**Frontend build:** `npm run build` inside `frontend/`, then copy `dist/` to `/var/www/cloudops-ai/`. The production build reads `frontend/.env.production` (`VITE_API_BASE_URL=/api/v1`); local development uses `frontend/.env` with the full server URL.

## 13. Connecting a real AWS account (IAM setup guide)

This is what a customer would do to connect their AWS account without sharing any keys.

**Step 1.** In the customer's AWS account, create an IAM policy allowing only Cost Explorer reads:

    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": ["ce:GetCostAndUsage"],
          "Resource": "*"
        }
      ]
    }

**Step 2.** Create an IAM Role and attach that policy. Give it this trust policy, replacing the placeholders with the platform's AWS account ID and the External ID generated by CloudOps AI for that connection:

    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": { "AWS": "arn:aws:iam::PLATFORM_ACCOUNT_ID:root" },
          "Action": "sts:AssumeRole",
          "Condition": {
            "StringEquals": { "sts:ExternalId": "EXTERNAL_ID_FROM_CLOUDOPS" }
          }
        }
      ]
    }

**Step 3.** Copy the Role ARN (for example `arn:aws:iam::123456789012:role/CloudOpsAIReadOnly`) and enter it on the Cloud Accounts page.

**Step 4.** CloudOps AI now assumes the role through STS whenever it syncs costs. The customer can revoke access at any time by deleting the role.

## 14. Local setup

Requirements: Python 3.12+, Node.js LTS, Docker Desktop.

    git clone https://github.com/mohamedashik110/cloudops-ai.git
    cd cloudops-ai
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

Create a `.env` file in the project root (see `.env.example`) with:

    DEBUG=True
    SECRET_KEY=any-long-random-string
    POSTGRES_DB=cloudops_ai
    POSTGRES_USER=cloudops_user
    POSTGRES_PASSWORD=choose-a-password
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    REDIS_URL=redis://localhost:6379/0
    AWS_ACCESS_KEY_ID=your-platform-aws-key
    AWS_SECRET_ACCESS_KEY=your-platform-aws-secret
    AWS_REGION=us-east-1
    GEMINI_API_KEY=your-gemini-key

Start Postgres and Redis, migrate, and run the API:

    docker compose up -d postgres redis
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver 8080

Optionally generate demo data for an organization:

    python manage.py generate_demo_data --org "Demo Org" --days 90

Run the frontend:

    cd frontend
    npm install
    npm run dev

## 15. Testing

    python manage.py test

17 automated tests cover:

- Authentication and RBAC in both directions (allowed roles succeed, disallowed roles get 403)
- Multi-tenant isolation (one organization cannot see another's data)
- Analytics correctness (the totals and rankings are mathematically right)
- CSV export
- ML forecasting, including the "not enough data" edge case
- Copilot request validation and grounded responses (a real call to Gemini)

The same suite runs automatically on every push in GitHub Actions.

## 16. Project structure

    cloudops-ai/
      config/            Django settings, URLs, Celery app
      common/            Shared permission classes and health check
      users/             Custom user model, organizations, JWT auth, RBAC
      cloud_accounts/    CloudAccount and CostRecord models, STS/AWS integration, Celery sync task
      analytics/         Cost aggregation, Redis caching, CSV report
      ml_engine/         Feature engineering, model training, forecasts
      ai_copilot/        Router / Analyst / Verifier agents and the chat endpoint
      frontend/          React (Vite) application
      docker-compose.yml Postgres, Redis, web, Celery
      Dockerfile         Application image (non-root user)
      .github/workflows/ CI pipeline

## 17. Engineering challenges and what I learned

The most valuable parts of this project were the real problems I had to diagnose:

- **AWS Cost Explorer data lag.** Requests ending "today" failed with a DataUnavailableException because recent days are not processed yet. I moved the query window back a few days.
- **A security flaw in my own design.** I noticed that storing customer AWS keys was unsafe and replaced it with STS AssumeRole plus External IDs, migrating the schema and updating every test and management command that depended on it.
- **Out-of-memory kills on a small instance.** Celery and Gunicorn workers were being SIGKILLed on a 1 GB instance. I diagnosed it from the logs, tuned worker concurrency, then moved to a larger instance.
- **Disk exhaustion.** Docker builds with pandas and scikit-learn filled an 8 GB disk; I resized the volume and grew the filesystem.
- **Code deployed but database not migrated.** The admin returned 500s because the running code expected a column that did not exist yet. Lesson: `git pull` updates code, never the schema.
- **Vite bakes environment variables in at build time.** My production build kept calling the wrong URL until I separated `.env` and `.env.production` and rebuilt.
- **API shape mismatch.** DRF serializes Decimal fields as strings and I had a nested-versus-flat field mismatch, which crashed the dashboard until I made the frontend defensive and correct.
- **Nginx permissions.** Serving files from a home directory failed with permission errors; the fix was the conventional `/var/www` location with correct ownership.
- **A verification bug in the AI pipeline.** The Verifier initially flagged correct answers because of comma formatting, day counts, years, and digits inside service names like S3.
- **Split-brain environments.** I repeatedly ran commands against my local Docker containers while believing I was on the server. I now always confirm which environment I am in before touching data.

## 18. Known limitations

I would rather state these plainly than have them discovered:

- **Single server.** One EC2 instance, no load balancer or auto-scaling. PostgreSQL runs in a container rather than a managed service like RDS, and there are no automated backups yet.
- **Cost sync is not scheduled.** The Celery sync task is implemented and was tested end to end against real AWS Cost Explorer, but periodic scheduling (Celery Beat) and a "sync now" button in the UI are not wired up yet. My personal AWS account had almost no real spend, so the demo uses clearly flagged synthetic data.
- **Simple forecast.** Linear regression with a held-constant rolling average. It forecasts total spend only, not per service, and it does not know about planned changes.
- **Narrow Copilot knowledge.** It sees only an aggregate summary (totals, top five services, the last ten days) plus the forecast. It cannot explain causes and has no conversation memory.
- **Heuristic Verifier.** It can occasionally over-flag an answer, and it checks numbers, not the logic of the sentence around them.
- **Token storage.** The frontend keeps the JWT in localStorage, which is convenient but exposed to XSS. A hardened version would use httpOnly cookies.
- **Manual deployment.** Deploys are done by SSH and Docker Compose rather than an automated CD pipeline.
- **Free-tier LLM.** The Copilot uses Gemini's free tier, so it is subject to rate limits and occasional 503 errors.

## 19. Roadmap

- Celery Beat scheduling and a UI trigger for cost sync
- Per-service forecasting, and predicted-versus-actual accuracy tracking
- Anomaly detection for unusual cost spikes
- Idle-resource detection with savings recommendations
- Streaming Copilot responses and multi-turn conversation memory
- Move PostgreSQL to RDS, add automated backups and monitoring alerts
- Automated deployment (CD) from GitHub Actions
- Multi-cloud support (GCP, Azure)
- httpOnly-cookie authentication

## Author

**Mohamed Ashik**
GitHub: https://github.com/mohamedashik110
