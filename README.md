# Auto-Job Profiling Applying

## Creator

This project was created, written, and maintained by **ANISH KUMAR**.
All primary documentation in this README is presented as the work of **ANISH KUMAR**.

Production-minded SaaS platform for job intake, candidate profiling, fit analysis, tailored resume generation, and application drafting.

## Stack

- Backend: FastAPI, SQLAlchemy, JWT auth
- Frontend: React + Vite
- Worker: Python modular AI pipeline runner
- Infra: Docker Compose, Dockerfiles, Kubernetes manifests

## Quick Start

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
cmd /c npm install
cmd /c npm run dev
```

```powershell
cd worker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.runner
```

Default login:

- `admin@autojobdemo.com`
- `ChangeMe123!`
