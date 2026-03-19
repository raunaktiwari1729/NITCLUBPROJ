# NIT Club Compass

## Quick Start

### 1. Backend
```powershell
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Mac / Linux
pip install -r requirements.txt
python seed_data.py
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Frontend (new terminal)
```powershell
cd frontend
python -m http.server 3000
```

Open **http://localhost:3000**

---

## Features
- Netflix-inspired Dark UI
- Club Discovery and Comparisons
- Events & Forum
- Staff & Owner Admin Portals
- **Forgot Password (OTP via EmailJS)**

---

## Accounts

| Role       | Credentials / How to sign up |
|------------|----------------|
| Student    | Any @nitkkr.ac.in email + sign up directly |
| Club Admin | Created via Admin Portal by Owner/Faculty |
| Faculty    | Created via Admin Portal by Owner |
| Owner (Admin) | Email set via `OWNER_EMAIL` env var — password set via `ADMIN_PASSWORD` env var |

> ⚠️ Never commit real credentials to this file. Set all secrets as environment variables.

---

## Environment Variables (Required for Production)
```
MONGO_URL=mongodb+srv://...        ← MongoDB Atlas connection string
JWT_SECRET_KEY=<random-40-chars>   ← Secret for signing JWT tokens
ADMIN_PASSWORD=<strong-password>   ← Owner login password
ADMIN_SENIOR_KEY=<random-string>   ← Secret key for faculty signup
CLUB_ADMIN_KEY=<random-string>     ← Secret key for club admin signup
OWNER_EMAIL=your@email.com         ← Owner account email
GROQ_API_KEY=gsk_...               ← Enables AI chatbot (optional)
```

> ⚠️ Never commit .env files or hardcode these values in code.

---

## Bugs Fixed (v6 → v7)

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | server.py | `datetime.utcnow()` deprecated — crashes on Python 3.12 | Replaced with `datetime.now(timezone.utc)` throughout |
| 2 | server.py | `GET /api/dm/{user_id}` registered **before** `/api/dm/threads/list` and `/api/dm/unread/count` — FastAPI matched "threads"/"unread" as user IDs | Reordered routes: specific paths first |
| 3 | server.py | `GET /api/posts/v2` registered **after** `GET /api/posts/{post_id}` — FastAPI matched "v2" as a post_id | Moved `/posts/anon` and `/posts/v2` before `/{post_id}` |
| 4 | server.py | `datetime.fromisoformat()` comparison crashed with timezone-aware strings | Added `_safe_dt()` helper for robust parsing |
| 5 | forum.html | Called `api.postsV2(q)` which **does not exist** in api.js — forum never loaded posts | Changed to `api.posts(q)` |
| 6 | All pages | AI Chat widget only initialised on `index.html` — missing on 10 other pages | Added `initChatWidget()` to every page |
| 7 | All pages | Cache-bust version `?v=6` inconsistent | Bumped to `?v=7` uniformly |
| 8 | messages.html | Search-results dropdown had no `position:relative` parent — appeared in wrong position | Added `position:relative` to wrapper div |
| 9 | All pages | No favicon | Added emoji favicon to all pages |
| 10 | forum.html | `setPostType()` used bare global `event` variable — breaks in strict mode / Firefox | Passed `event` explicitly through `onclick` |
