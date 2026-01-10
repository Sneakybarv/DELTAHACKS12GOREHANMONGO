This file has been moved to `docs/README_FOR_JUDGES.md`.
Please open the documentation in the `docs/` directory.

Prerequisites
-------------
- macOS (instructions target macOS but are similar on Linux)
- Git
- Node.js 18+ and npm
- Python 3.10+ (Python 3.11/3.12 recommended)
- Homebrew (optional, used to install Tesseract if OCR is used)
- A MongoDB Atlas connection string (for persistence). If you don't have Atlas, the app will run but some features requiring DB will fail.

Repository layout (important paths)
- Root: contains this README and helper scripts
- `backend/`: FastAPI backend
- `frontend/`: Next.js frontend
- `scripts/reset_and_run.sh`: stops/starts backend + frontend and writes logs/PIDs

Quick Start (recommended)
-------------------------
1. Clone the repo and cd into it:

   git clone <repo-url>
   cd DELTAHACKSrealREHAN

2. Configure backend environment variables.
   - Copy a `.env` file into `backend/`. At minimum set:

     MONGODB_URI="your_mongo_uri_here"

   - Optionally add `GEMINI_API_KEY` if available. For demos, the service falls back to OCR/mock parsing.

3. Run the automated start script (recommended):

   bash scripts/reset_and_run.sh

   - This will stop any processes on ports 8000 and 3002, create `logs/`, start the backend on port 8000 and the frontend on port 3002. PIDs are written to `.local/pids/` and logs to `logs/`.

4. Verify both services: open these URLs in a browser:
   - Backend (API root): http://localhost:8000/
   - Frontend: http://localhost:3002/

Manual start (if you prefer):

- Backend (from repo root):

  cd backend
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  export $(cat .env | sed 's/#.*//' | xargs)
  PYTHONPATH=$(pwd) uvicorn main:app --reload --host 0.0.0.0 --port 8000

- Frontend (from repo root):

  cd frontend
  npm install
  npm run dev -- -p 3002

Quick verification (examples)
-----------------------------
- Check backend health:

  curl http://localhost:8000/

- Update user profile (example):

  curl -X POST http://localhost:8000/api/user/profile \
    -H "Content-Type: application/json" \
    -d '{"allergies":["Peanuts"],"dietary_preferences":["Vegan"],"health_goals":["Run 3x/week"]}'

- Fetch backend logs (development only):

  curl http://localhost:8000/api/debug/logs

Notes for judges
----------------
- The backend exposes a development logs endpoint only when `ENVIRONMENT` is not `production`. This lets collaborators fetch recent logs without accessing the host machine.
- If a profile save returns an error, paste the response and then fetch `/api/debug/logs` to see the backend trace.
- For demo convenience, the frontend uses an `X-User-Id` header (or localStorage) to associate receipts with a user. No authentication is required in this demo. Do not use these mechanisms in production.

Troubleshooting
---------------
- If the backend fails to connect to MongoDB, ensure `MONGODB_URI` is correct and the Atlas cluster allows your IP.
- If Firefox/Chrome cannot reach the frontend, confirm the Next process is running on port 3002 (or use the start script).
- If OCR is required and Tesseract is missing, install via Homebrew:

  brew install tesseract

Contact
-------
If anything above fails during the judging session, collect the following and share with the team:
- `curl` response from the failing endpoint
- Output of `curl http://localhost:8000/api/debug/logs`
- Contents of `backend/.env` (redact secrets before sharing)

Thank you — good luck with judging!

Judge API Keys
--------------
For security, judges should never receive third-party service keys. Instead, the owner issues short-lived judge API tokens which the judge includes in requests via the `X-Api-Key` header.

How it works (owner):
- Set an `ADMIN_KEY` environment variable on the machine running the backend.
- Call the admin endpoint to create a judge token (the token is shown once):

```bash
export ADMIN_KEY="your_admin_key_here"
bash scripts/issue_judge_key.sh judge_name 24
```

The script calls `POST /api/admin/issue-key` and prints a JSON response containing the plaintext `token` (store it securely; it will expire).

How judges use the token:
- Include the token in requests with the `X-Api-Key` header.

Example: update profile (judge):

```bash
curl -X POST http://localhost:8000/api/user/profile \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: <judge-token-here>" \
  -d '{"allergies":["Peanuts"],"dietary_preferences":["Vegan"],"health_goals":["Run 3x/week"]}'
```

Example: upload receipt (judge):

```bash
curl -X POST http://localhost:8000/api/receipts/upload \
  -H "X-Api-Key: <judge-token-here>" \
  -H "X-User-Id: judge1" \
  -F "file=@/path/to/receipt.jpg"
```

Security notes:
- Tokens are short-lived and can be revoked by the owner (admin).
- The owner should provide tokens to judges over a secure channel and never embed them in public places.

