from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import jwt, bcrypt, os, re, secrets, string




MONGO_URL        = os.environ.get("MONGO_URL",          "mongodb://localhost:27017")
DB_NAME          = os.environ.get("DB_NAME",            "college_club_compass")
JWT_SECRET       = os.environ.get("JWT_SECRET_KEY",     "default-dev-secret-change-me-in-production")
ADMIN_SENIOR_KEY = os.environ.get("ADMIN_SENIOR_KEY",   "default-senior-key")
CLUB_ADMIN_KEY   = os.environ.get("CLUB_ADMIN_KEY",     "default-club-key")
ADMIN_PASSWORD   = os.environ.get("ADMIN_PASSWORD",     "admin123")
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY")
COLLEGE_DOMAIN   = os.environ.get("COLLEGE_DOMAIN",     "nitkkr.ac.in")
OWNER_EMAIL      = os.environ.get("OWNER_EMAIL",        "raunaktiwari1729@gmail.com")


def _safe_dt(s: str) -> datetime:
    """Parse ISO string from DB → naive UTC datetime for comparison."""
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except Exception:
        return datetime.now(timezone.utc).replace(tzinfo=None)

# Roll prefix → year mapping
YEAR_PREFIX_MAP = {"1251": 1, "1241": 2, "1231": 2, "1221": 3, "1211": 4}

# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="NIT KKR Club Compass API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nit-club-compass-1.onrender.com",
        "http://localhost:3000",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

db = AsyncIOMotorClient(MONGO_URL)[DB_NAME]
security = HTTPBearer(auto_error=False)

# ── Helpers ───────────────────────────────────────────────────────────────────
def extract_roll_info(roll: str):
    roll = roll.strip().upper()
    prefix = roll[:4]
    year = YEAR_PREFIX_MAP.get(prefix)
    branch_code = roll[4:6] if len(roll) >= 6 else "??"
    branch_map = {"01":"CE","02":"CS","03":"IT","04":"EE","05":"EC","06":"ME","07":"PI","08":"AI","09":"II","10":"MC","11":"RA","12":"AD","13":"MV","14":"SE","15":"BA","16":"MCA","17":"MBA","18":"MSc","19":"PhD"}
    branch = branch_map.get(branch_code, branch_code)
    return year, branch, prefix

def validate_college_email(email: str):
    return email.lower().endswith(f"@{COLLEGE_DOMAIN}")

def is_owner_email(email: str):
    return email.lower() == OWNER_EMAIL.lower()

def make_token(uid, role):
    return jwt.encode(
        {"sub": uid, "role": role, "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        JWT_SECRET, algorithm="HS256"
    )

def read_token(tok):
    try:    return jwt.decode(tok, JWT_SECRET, algorithms=["HS256"])
    except: return None

def gen_otp():
    return ''.join(secrets.choice(string.digits) for _ in range(6))

async def current_user(cred: HTTPAuthorizationCredentials = Depends(security)):
    if not cred: raise HTTPException(401, "Not authenticated")
    p = read_token(cred.credentials)
    if not p: raise HTTPException(401, "Invalid token")
    u = await db.users.find_one({"_id": p["sub"]})
    if not u: raise HTTPException(401, "User not found")
    return u

async def optional_user(cred: HTTPAuthorizationCredentials = Depends(security)):
    if not cred: return None
    p = read_token(cred.credentials)
    return await db.users.find_one({"_id": p["sub"]}) if p else None

async def require_club_admin(u=Depends(current_user)):
    if u.get("role") not in ("club_admin", "owner", "faculty_incharge"):
        raise HTTPException(403, "Club admin access required")
    return u

def clean(doc):
    if doc: doc["id"] = doc.pop("_id")
    return doc

def fmt_user(u):
    return {
        "id": u["_id"], "name": u["name"], "email": u["email"],
        "role": u["role"], "roll_number": u.get("roll_number",""),
        "year": u.get("year"), "branch": u.get("branch",""),
        "verified": u.get("verified", False),
        "email_verified": u.get("email_verified", False),
        "bio": u.get("bio", ""),
        "managed_club_id": u.get("managed_club_id", ""),
        "department": u.get("department", ""),
    }

# ── Models ────────────────────────────────────────────────────────────────────
class SignupModel(BaseModel):
    name: str; email: str; password: str
    role: str  # student | club_admin | faculty_incharge
    roll_number: str
    secret_key: Optional[str] = None

class LoginModel(BaseModel):
    email: str; password: str

class VerifyEmailModel(BaseModel):
    email: str; otp: str

class QuizSubmitModel(BaseModel):
    answers: List[int]

class BookmarkModel(BaseModel):
    club_id: str

class WatchlistModel(BaseModel):
    club_id: str; note: Optional[str] = ""

class ChatMessage(BaseModel):
    message: str; context: Optional[str] = ""

class ClubUpdateModel(BaseModel):
    name: Optional[str]=None; tagline: Optional[str]=None
    description: Optional[str]=None; members: Optional[int]=None
    email: Optional[str]=None; tags: Optional[List[str]]=None
    icon: Optional[str]=None; founded: Optional[int]=None
    image_url: Optional[str]=None; events: Optional[List[str]]=None
    recruitment_info: Optional[str]=None

class ClubCreateModel(BaseModel):
    name: str; domain: str; tagline: str; description: str
    members: int=0; founded: int=2020; email: str=""
    tags: List[str]=[]; icon: str="🎯"
    image_url: Optional[str]=None; events: Optional[List[str]]=[]
    recruitment_info: Optional[str]=""

class PostModel(BaseModel):
    title: str; body: str; tags: List[str]=[]; club_id: Optional[str]=None

class CommentModel(BaseModel):
    body: str

class DMModel(BaseModel):
    to_user_id: str; body: str

class ProfileUpdateModel(BaseModel):
    name: Optional[str]=None; bio: Optional[str]=None

# ── SIGNUP / AUTH ─────────────────────────────────────────────────────────────
@app.post("/api/auth/signup")
async def signup(d: SignupModel, bg: BackgroundTasks):
    email = d.email.lower().strip()
    roll  = d.roll_number.strip().upper()

    # Owner bypass — any email allowed
    owner_mode = is_owner_email(email)

    if not owner_mode and not validate_college_email(email):
        raise HTTPException(400, f"Only @{COLLEGE_DOMAIN} emails allowed")

    year, branch, prefix = extract_roll_info(roll)
    # For staff/owner, roll number is optional — accept any format
    if not owner_mode and roll not in ("STAFF", "FACULTY") and not year:
        raise HTTPException(400, f"Unrecognised roll number prefix '{prefix}'. Must be 1211/1221/1231/1241/1251")

    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")

    role = d.role.lower()
    # Normalize legacy 'senior' role to 'student' — year is auto-detected from roll number
    if role == "senior":
        role = "student"
    if role not in ("student", "club_admin", "faculty_incharge"):
        raise HTTPException(400, "Invalid role")

    if role == "club_admin" and d.secret_key != CLUB_ADMIN_KEY:
        raise HTTPException(400, "Invalid club admin key")

    if role == "faculty_incharge" and d.secret_key != ADMIN_SENIOR_KEY:
        raise HTTPException(400, "Invalid faculty key — contact administrator")

    # Owner gets promoted to owner role
    if owner_mode:
        role = "owner"

    pw_hash = bcrypt.hashpw(d.password.encode(), bcrypt.gensalt()).decode()
    uid = str(ObjectId())

    await db.users.insert_one({
        "_id": uid, "name": d.name, "email": email,
        "password": pw_hash, "role": role,
        "roll_number": roll, "year": year, "branch": branch,
        "email_verified": True,  # no OTP — auto-verified
        "verified": True,
        "bookmarks": [], "watchlist": [], "quiz_result": None,
        "bio": "", "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    })

    token = make_token(uid, role)
    return {"message": "Account created!", "token": token, "user": fmt_user(await db.users.find_one({"_id": uid}))}

@app.post("/api/auth/verify-email")
async def verify_email(d: VerifyEmailModel):
    email = d.email.lower().strip()
    user  = await db.users.find_one({"email": email})
    if not user: raise HTTPException(404, "User not found")
    if user.get("email_verified"): raise HTTPException(400, "Already verified")

    if user.get("otp") != d.otp:
        raise HTTPException(400, "Incorrect OTP")
    if datetime.now(timezone.utc).replace(tzinfo=None) > _safe_dt(user["otp_expiry"]):
        raise HTTPException(400, "OTP expired. Request a new one.")

    await db.users.update_one({"email": email}, {"$set": {"email_verified": True, "otp": None}})
    token = make_token(user["_id"], user["role"])
    updated = await db.users.find_one({"_id": user["_id"]})
    return {"message": "Email verified!", "token": token, "user": fmt_user(updated)}

@app.post("/api/auth/resend-otp")
async def resend_otp(data: dict):
    email = data.get("email","").lower().strip()
    user  = await db.users.find_one({"email": email})
    if not user: raise HTTPException(404, "User not found")
    if user.get("email_verified"): raise HTTPException(400, "Already verified")

    otp = gen_otp()
    await db.users.update_one({"email": email}, {"$set": {
        "otp": otp, "otp_expiry": (datetime.now(timezone.utc)+timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    }})
    print(f"📧 New OTP for {email}: {otp}")
    return {"message": "OTP sent. Check backend console (dev mode)."}

@app.post("/api/auth/login")
async def login(d: LoginModel):
    email = d.email.lower().strip()
    
    # Owner login logic:
    if is_owner_email(email):
        if d.password == ADMIN_PASSWORD:
            user = await db.users.find_one({"email": email})
            # Auto-create if doesn't exist to ensure fully working state
            if not user:
                pw_hash = bcrypt.hashpw(d.password.encode(), bcrypt.gensalt()).decode()
                uid = str(ObjectId())
                await db.users.insert_one({
                    "_id": uid, "name": "Super Admin", "email": email,
                    "password": pw_hash, "role": "owner",
                    "email_verified": True, "verified": True,
                    "bookmarks": [], "watchlist": [],
                    "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                })
                user = await db.users.find_one({"email": email})
            token = make_token(user["_id"], user["role"])
            return {"token": token, "user": fmt_user(user)}

    user = await db.users.find_one({"email": email})
    if not user or not bcrypt.checkpw(d.password.encode(), user["password"].encode()):
        raise HTTPException(401, "Wrong email or password")
    token = make_token(user["_id"], user["role"])
    return {"token": token, "user": fmt_user(user)}

class ResetRequestModel(BaseModel):
    email: str

class ResetConfirmModel(BaseModel):
    email: str; otp: str; new_password: str

@app.post("/api/auth/reset-password-request")
async def reset_password_request(d: ResetRequestModel):
    email = d.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user: raise HTTPException(404, "User not found")
    
    otp = gen_otp()
    await db.users.update_one({"email": email}, {"$set": {
        "reset_otp": otp, 
        "reset_otp_expiry": (datetime.now(timezone.utc)+timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    }})
    print(f"🔑 Password reset OTP for {email}: {otp}")
    return {"message": "OTP sent", "user_first_name": user["name"].split(' ')[0]}

@app.post("/api/auth/reset-password-confirm")
async def reset_password_confirm(d: ResetConfirmModel):
    email = d.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user: raise HTTPException(404, "User not found")
    
    if user.get("reset_otp") != d.otp:
        raise HTTPException(400, "Incorrect OTP")
    if datetime.now(timezone.utc).replace(tzinfo=None) > _safe_dt(user.get("reset_otp_expiry", "2000-01-01T00:00:00Z")):
        raise HTTPException(400, "OTP expired. Request a new one.")
    if len(d.new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    
    pw_hash = bcrypt.hashpw(d.new_password.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({"email": email}, {"$set": {
        "password": pw_hash, 
        "reset_otp": None, 
        "reset_otp_expiry": None
    }})
    return {"message": "Password updated successfully"}

@app.get("/api/auth/me")
async def me(u=Depends(current_user)):
    return fmt_user(u)

@app.patch("/api/auth/profile")
async def update_profile(d: ProfileUpdateModel, u=Depends(current_user)):
    upd = {}
    if d.name: upd["name"] = d.name
    if d.bio is not None: upd["bio"] = d.bio
    if upd: await db.users.update_one({"_id": u["_id"]}, {"$set": upd})
    return fmt_user(await db.users.find_one({"_id": u["_id"]}))

# ── USERS ──────────────────────────────────────────────────────────────────────
@app.get("/api/users/search")
async def search_users(q: str = Query(...), u=Depends(current_user)):
    q = re.escape(q.strip())
    users = await db.users.find({
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"roll_number": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10).to_list(10)
    return [fmt_user(x) for x in users if x["_id"] != u["_id"]]

@app.get("/api/users/{user_id}")
async def get_user(user_id: str, u=Depends(current_user)):
    target = await db.users.find_one({"_id": user_id})
    if not target: raise HTTPException(404, "User not found")
    return fmt_user(target)

# ── CLUBS ──────────────────────────────────────────────────────────────────────
@app.get("/api/clubs")
async def get_clubs(domain: Optional[str]=None, search: Optional[str]=None):
    q = {}
    if domain: q["domain"] = domain
    if search: q["name"] = {"$regex": re.escape(search), "$options": "i"}
    clubs = await db.clubs.find(q).to_list(200)
    return [clean(c) for c in clubs]

@app.get("/api/clubs/{club_id}")
async def get_club(club_id: str):
    c = await db.clubs.find_one({"_id": club_id})
    if not c: raise HTTPException(404, "Club not found")
    return clean(c)

@app.patch("/api/clubs/{club_id}")
async def update_club(club_id: str, d: ClubUpdateModel, u=Depends(require_club_admin)):
    # Owners and faculty can edit any club; club_admins can only edit their own assigned club
    if u.get("role") not in ("owner", "faculty_incharge"):
        if u.get("managed_club_id") != club_id:
            raise HTTPException(403, "You can only edit your own club")
    upd = {k: v for k, v in d.dict().items() if v is not None}
    if not upd: raise HTTPException(400, "Nothing to update")
    await db.clubs.update_one({"_id": club_id}, {"$set": upd})
    c = await db.clubs.find_one({"_id": club_id})
    return clean(c)

@app.delete("/api/clubs/{club_id}")
async def delete_club(club_id: str, u=Depends(require_club_admin)):
    if u.get("role") not in ("owner", "faculty_incharge"):
        if u.get("managed_club_id") != club_id:
            raise HTTPException(403, "You can only delete your own club")
    await db.clubs.delete_one({"_id": club_id})
    return {"ok": True}

@app.post("/api/clubs")
async def create_club(d: ClubCreateModel, u=Depends(require_club_admin)):
    COLORS = {"Technical":"#6366f1","Cultural":"#ec4899","Sports":"#f97316","Literary":"#14b8a6","Social":"#22c55e","Management":"#f59e0b"}
    cid = str(ObjectId())
    doc = {"_id": cid, "color": COLORS.get(d.domain,"#888"), **d.dict(), "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'}
    await db.clubs.insert_one(doc)
    return clean(await db.clubs.find_one({"_id": cid}))

# ── QUIZ ───────────────────────────────────────────────────────────────────────
QUIZ_QUESTIONS = [
    {"id":1,"text":"What type of activity excites you most?","opts":["Building apps/websites","Performing on stage","Competing in sports","Solving real-world problems"]},
    {"id":2,"text":"How do you prefer to spend free time?","opts":["Coding or tinkering","Dancing/singing/acting","Outdoor sports/gym","Reading/writing/debating"]},
    {"id":3,"text":"Which skill do you most want to develop?","opts":["Technical/coding skills","Creative/artistic skills","Leadership & teamwork","Communication & writing"]},
    {"id":4,"text":"Your ideal club activity would be?","opts":["Hackathon overnight","Cultural fest performance","Inter-college tournament","Community service drive"]},
    {"id":5,"text":"You're most comfortable when?","opts":["Solving logical puzzles","Expressing yourself creatively","Playing as part of a team","Helping others learn"]},
    {"id":6,"text":"Pick your ideal college memory?","opts":["Winning a coding contest","Rocking the stage at Confluence","Winning at Techspardha sports","Volunteering at an outreach camp"]},
    {"id":7,"text":"What kind of impact do you want to make?","opts":["Build products that matter","Inspire through art/culture","Represent college at sports","Make someone's life better"]},
    {"id":8,"text":"Your friends would describe you as?","opts":["The tech geek","The creative soul","The sporty one","The thoughtful one"]},
    {"id":9,"text":"What do you value most in a club?","opts":["Learning new technical skills","Expressing creativity","Physical fitness & competition","Community & social impact"]},
    {"id":10,"text":"How do you handle pressure?","opts":["Dive into problem-solving","Channel it into performance","Push harder physically","Talk it out and support others"]},
]

@app.get("/api/quiz/questions")
async def questions():
    return QUIZ_QUESTIONS

@app.post("/api/quiz/submit")
async def submit_quiz(d: QuizSubmitModel, u=Depends(current_user)):
    import httpx
    scores = {"Technical":0,"Cultural":0,"Sports":0,"Literary":0,"Social":0,"Management":0}
    domain_map = [
        ["Technical","Cultural","Sports","Social"],
        ["Technical","Cultural","Sports","Literary"],
        ["Technical","Cultural","Sports","Literary"],
        ["Technical","Cultural","Sports","Social"],
        ["Technical","Cultural","Sports","Social"],
        ["Technical","Cultural","Sports","Social"],
        ["Technical","Cultural","Sports","Social"],
        ["Technical","Cultural","Sports","Literary"],
        ["Technical","Cultural","Sports","Social"],
        ["Technical","Cultural","Sports","Social"],
    ]
    for i, ans in enumerate(d.answers[:10]):
        if 0 <= ans <= 3 and i < len(domain_map):
            domain = domain_map[i][ans]
            scores[domain] += 1

    sorted_domains = sorted(scores.items(), key=lambda x: -x[1])
    top_domain = sorted_domains[0][0]

    clubs = await db.clubs.find({"domain": top_domain}).to_list(5)
    fallback = await db.clubs.find({}).limit(5).to_list(5)
    recommended = clubs[:3] if len(clubs) >= 3 else clubs + fallback[:3-len(clubs)]
    rec_ids = [c["_id"] for c in recommended]

    result = {
        "scores": scores, "top_domain": top_domain,
        "recommended_club_ids": rec_ids,
        "ai_summary": f"Based on your answers, you lean towards {top_domain} activities! You'd thrive in clubs that match your passion for {'building and creating technology' if top_domain=='Technical' else 'creative expression and performance' if top_domain=='Cultural' else 'sports and physical competition' if top_domain=='Sports' else 'literature and debate' if top_domain=='Literary' else 'community impact' if top_domain=='Social' else 'leadership and entrepreneurship'}."
    }

    await db.users.update_one({"_id": u["_id"]}, {"$set": {"quiz_result": result}})
    return result

@app.get("/api/quiz/result")
async def quiz_result(u=Depends(current_user)):
    r = u.get("quiz_result")
    if not r: raise HTTPException(404, "No quiz result yet")
    rec_clubs = []
    for cid in r.get("recommended_club_ids", []):
        c = await db.clubs.find_one({"_id": cid})
        if c: rec_clubs.append(clean(c))
    return {**r, "recommended_clubs": rec_clubs}

# ── BOOKMARKS & WATCHLIST ──────────────────────────────────────────────────────
@app.post("/api/bookmarks")
async def add_bookmark(d: BookmarkModel, u=Depends(current_user)):
    await db.users.update_one({"_id": u["_id"]}, {"$addToSet": {"bookmarks": d.club_id}})
    return {"ok": True}

@app.get("/api/bookmarks")
async def get_bookmarks(u=Depends(current_user)):
    ids = u.get("bookmarks", [])
    clubs = [clean(c) for c in [await db.clubs.find_one({"_id": i}) for i in ids] if c]
    return clubs

@app.delete("/api/bookmarks/{club_id}")
async def remove_bookmark(club_id: str, u=Depends(current_user)):
    await db.users.update_one({"_id": u["_id"]}, {"$pull": {"bookmarks": club_id}})
    return {"ok": True}

@app.post("/api/watchlist")
async def add_watchlist(d: WatchlistModel, u=Depends(current_user)):
    entry = {"club_id": d.club_id, "note": d.note or "", "added_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'}
    await db.users.update_one({"_id": u["_id"]}, {"$pull": {"watchlist": {"club_id": d.club_id}}})
    await db.users.update_one({"_id": u["_id"]}, {"$push": {"watchlist": entry}})
    return {"ok": True}

@app.get("/api/watchlist")
async def get_watchlist(u=Depends(current_user)):
    result = []
    for item in u.get("watchlist", []):
        c = await db.clubs.find_one({"_id": item["club_id"]})
        if c: result.append({**clean(c), "note": item.get("note",""), "added_at": item.get("added_at","")})
    return result

@app.patch("/api/watchlist/{club_id}")
async def update_note(club_id: str, d: WatchlistModel, u=Depends(current_user)):
    await db.users.update_one(
        {"_id": u["_id"], "watchlist.club_id": club_id},
        {"$set": {"watchlist.$.note": d.note}}
    )
    return {"ok": True}

@app.delete("/api/watchlist/{club_id}")
async def remove_watchlist(club_id: str, u=Depends(current_user)):
    await db.users.update_one({"_id": u["_id"]}, {"$pull": {"watchlist": {"club_id": club_id}}})
    return {"ok": True}

# ── FORUM (Reddit-style) ───────────────────────────────────────────────────────
async def enrich_post(post, current_uid=None):
    author = await db.users.find_one({"_id": post.get("author_id")})
    count  = await db.comments.count_documents({"post_id": post["_id"]})
    return {
        "id": post["_id"], "title": post["title"], "body": post["body"],
        "tags": post.get("tags",[]), "club_id": post.get("club_id"),
        "upvotes": len(post.get("upvotes",[])),
        "upvoted": current_uid in post.get("upvotes",[]) if current_uid else False,
        "comment_count": count,
        "author": fmt_user(author) if author else {"name":"[deleted]","role":"student"},
        "created_at": post.get("created_at",""),
    }

@app.get("/api/posts")
async def get_posts(tag: Optional[str]=None, club_id: Optional[str]=None,
                    sort: str="new", u=Depends(optional_user)):
    q = {}
    if tag: q["tags"] = tag
    if club_id: q["club_id"] = club_id
    posts = await db.posts.find(q).to_list(100)
    if sort == "top":
        posts.sort(key=lambda p: len(p.get("upvotes",[])), reverse=True)
    else:
        posts.sort(key=lambda p: p.get("created_at",""), reverse=True)
    uid = u["_id"] if u else None
    vrole = u.get("role") if u else None
    return [await enrich_post_v2(p, uid, vrole) for p in posts]

@app.post("/api/posts")
async def create_post(d: PostModel, u=Depends(current_user)):
    if not u.get("email_verified"): raise HTTPException(403, "Email not verified")
    pid = str(ObjectId())
    await db.posts.insert_one({
        "_id": pid, "title": d.title, "body": d.body,
        "tags": d.tags, "club_id": d.club_id,
        "author_id": u["_id"], "upvotes": [],
        "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    })
    return await enrich_post(await db.posts.find_one({"_id": pid}), u["_id"])

@app.post("/api/posts/anon")
async def create_anon_post(d: PostModel, u=Depends(current_user)):
    if not u.get("email_verified"): raise HTTPException(403, "Email not verified")
    pid = str(ObjectId())
    await db.posts.insert_one({
        "_id": pid, "title": d.title, "body": d.body,
        "tags": d.tags, "club_id": d.club_id,
        "author_id": u["_id"], "anonymous": True, "upvotes": [],
        "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    })
    post = await db.posts.find_one({"_id": pid})
    return {
        "id": pid, "title": post["title"], "body": post["body"],
        "tags": post.get("tags",[]), "club_id": post.get("club_id"),
        "upvotes": 0, "upvoted": False, "comment_count": 0,
        "author": {"name": "Anonymous", "role": "student"},
        "anonymous": True, "created_at": post["created_at"]
    }

# Patch enrich_post to handle anonymous
async def enrich_post_v2(post, current_uid=None, viewer_role=None):
    count = await db.comments.count_documents({"post_id": post["_id"]})
    is_anon = post.get("anonymous", False)
    real_name = None
    if is_anon:
        author_data = {"name": "Anonymous", "role": "student", "year": None, "branch": "", "roll_number": ""}
        # Reveal real name only to seniors/admins/owner
        if viewer_role in ("faculty_incharge", "club_admin", "owner"):
            real_author = await db.users.find_one({"_id": post.get("author_id")})
            if real_author:
                real_name = real_author.get("name", "")
    else:
        author = await db.users.find_one({"_id": post.get("author_id")})
        author_data = fmt_user(author) if author else {"name": "[deleted]", "role": "student"}
    result = {
        "id": post["_id"], "title": post["title"], "body": post["body"],
        "tags": post.get("tags",[]), "club_id": post.get("club_id"),
        "upvotes": len(post.get("upvotes",[])),
        "upvoted": current_uid in post.get("upvotes",[]) if current_uid else False,
        "comment_count": count, "author": author_data,
        "anonymous": is_anon, "created_at": post.get("created_at",""),
    }
    if real_name:
        result["real_name"] = real_name
    return result

# Override get_posts to use v2

@app.get("/api/posts/v2")
async def get_posts_v2(tag: Optional[str]=None, club_id: Optional[str]=None,
                       sort: str="new", u=Depends(optional_user)):
    q = {}
    if tag: q["tags"] = tag
    if club_id: q["club_id"] = club_id
    posts = await db.posts.find(q).to_list(100)
    if sort == "top":
        posts.sort(key=lambda p: len(p.get("upvotes",[])), reverse=True)
    else:
        posts.sort(key=lambda p: p.get("created_at",""), reverse=True)
    uid = u["_id"] if u else None
    vrole = u.get("role") if u else None
    return [await enrich_post_v2(p, uid, vrole) for p in posts]

# ── REVIEWS & RATINGS ─────────────────────────────────────────────────────────

@app.get("/api/posts/{post_id}")
async def get_post(post_id: str, u=Depends(optional_user)):
    p = await db.posts.find_one({"_id": post_id})
    if not p: raise HTTPException(404, "Post not found")
    return await enrich_post(p, u["_id"] if u else None)

@app.post("/api/posts/{post_id}/upvote")
async def upvote_post(post_id: str, u=Depends(current_user)):
    p = await db.posts.find_one({"_id": post_id})
    if not p: raise HTTPException(404)
    uid = u["_id"]
    if uid in p.get("upvotes",[]):
        await db.posts.update_one({"_id": post_id}, {"$pull": {"upvotes": uid}})
    else:
        await db.posts.update_one({"_id": post_id}, {"$addToSet": {"upvotes": uid}})
    updated = await db.posts.find_one({"_id": post_id})
    return {"upvotes": len(updated.get("upvotes",[])), "upvoted": uid in updated.get("upvotes",[])}

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: str, u=Depends(current_user)):
    p = await db.posts.find_one({"_id": post_id})
    if not p: raise HTTPException(404)
    if p["author_id"] != u["_id"] and u.get("role") not in ("faculty_incharge","club_admin","owner"):
        raise HTTPException(403, "Not allowed")
    await db.posts.delete_one({"_id": post_id})
    await db.comments.delete_many({"post_id": post_id})
    return {"ok": True}

@app.get("/api/posts/{post_id}/comments")
async def get_comments(post_id: str, u=Depends(optional_user)):
    comments = await db.comments.find({"post_id": post_id}).to_list(200)
    comments.sort(key=lambda c: c.get("created_at",""))
    result = []
    for c in comments:
        author = await db.users.find_one({"_id": c.get("author_id")})
        result.append({
            "id": c["_id"], "body": c["body"],
            "author": fmt_user(author) if author else {"name":"[deleted]","role":"student"},
            "created_at": c.get("created_at",""),
            "can_delete": u and (c["author_id"]==u["_id"] or u.get("role") in ("faculty_incharge","club_admin","owner"))
        })
    return result

@app.post("/api/posts/{post_id}/comments")
async def add_comment(post_id: str, d: CommentModel, u=Depends(current_user)):
    if not u.get("email_verified"): raise HTTPException(403, "Email not verified")
    p = await db.posts.find_one({"_id": post_id})
    if not p: raise HTTPException(404)
    cid = str(ObjectId())
    await db.comments.insert_one({
        "_id": cid, "post_id": post_id, "body": d.body,
        "author_id": u["_id"], "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    })
    c = await db.comments.find_one({"_id": cid})
    author = await db.users.find_one({"_id": c["author_id"]})
    return {"id": cid, "body": c["body"], "author": fmt_user(author), "created_at": c["created_at"], "can_delete": True}

@app.delete("/api/comments/{comment_id}")
async def delete_comment(comment_id: str, u=Depends(current_user)):
    c = await db.comments.find_one({"_id": comment_id})
    if not c: raise HTTPException(404)
    if c["author_id"] != u["_id"] and u.get("role") not in ("faculty_incharge","club_admin","owner"):
        raise HTTPException(403)
    await db.comments.delete_one({"_id": comment_id})
    return {"ok": True}

# ── DIRECT MESSAGES ────────────────────────────────────────────────────────────
@app.post("/api/dm")
async def send_dm(d: DMModel, u=Depends(current_user)):
    if not u.get("email_verified"): raise HTTPException(403, "Email not verified")
    target = await db.users.find_one({"_id": d.to_user_id})
    if not target: raise HTTPException(404, "User not found")
    mid = str(ObjectId())
    await db.messages.insert_one({
        "_id": mid, "from_id": u["_id"], "to_id": d.to_user_id,
        "body": d.body, "read": False,
        "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    })
    return {"id": mid, "ok": True}


@app.get("/api/dm/threads/list")
async def get_threads(u=Depends(current_user)):
    uid = u["_id"]
    msgs = await db.messages.find({"$or": [{"from_id": uid}, {"to_id": uid}]}).to_list(1000)
    threads = {}
    for m in sorted(msgs, key=lambda x: x.get("created_at","")):
        other = m["to_id"] if m["from_id"]==uid else m["from_id"]
        threads[other] = {"last_msg": m["body"], "last_time": m.get("created_at",""),
                          "unread": (not m["read"] and m["to_id"]==uid)}
    result = []
    for other_id, info in threads.items():
        other_user = await db.users.find_one({"_id": other_id})
        if other_user:
            result.append({"user": fmt_user(other_user), **info})
    result.sort(key=lambda x: x["last_time"], reverse=True)
    return result


@app.get("/api/dm/unread/count")
async def unread_count(u=Depends(current_user)):
    count = await db.messages.count_documents({"to_id": u["_id"], "read": False})
    return {"count": count}

# ── AI CHAT ────────────────────────────────────────────────────────────────────

@app.get("/api/dm/{user_id}")
async def get_dm_thread(user_id: str, u=Depends(current_user)):
    uid = u["_id"]
    msgs = await db.messages.find({
        "$or": [{"from_id": uid, "to_id": user_id}, {"from_id": user_id, "to_id": uid}]
    }).to_list(500)
    msgs.sort(key=lambda m: m.get("created_at",""))
    await db.messages.update_many({"from_id": user_id, "to_id": uid, "read": False}, {"$set": {"read": True}})
    return [{"id": m["_id"], "from_id": m["from_id"], "body": m["body"],
             "read": m["read"], "created_at": m.get("created_at","")} for m in msgs]

@app.post("/api/chat")
async def chat(d: ChatMessage, u=Depends(optional_user)):
    import httpx
    clubs = await db.clubs.find({}).to_list(50)
    club_summary = "\n".join([f"- {c['name']} ({c['domain']}): {c['tagline']}" for c in clubs])
    sys_prompt = f"""You are the NIT Kurukshetra Club Compass assistant. Help students explore clubs.
Available clubs at NIT KKR:
{club_summary}
Be friendly, helpful, and concise. Keep responses under 200 words."""

    if not GROQ_API_KEY:
        return {"reply": "AI chat requires GROQ_API_KEY configuration. Please add your Groq API key."}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model":"llama-3.3-70b-versatile","messages":[{"role":"system","content":sys_prompt},{"role":"user","content":d.message}],"max_tokens":300}
            )
            resp = r.json()
            if "choices" in resp:
                return {"reply": resp["choices"][0]["message"]["content"]}
            err_msg = resp.get("error", {}).get("message", str(resp))
            print(f"[GROQ ERROR] {err_msg}")
            return {"reply": f"AI error: {err_msg}"}
    except httpx.TimeoutException:
        return {"reply": "AI timed out. Please try again."}
    except Exception as e:
        print(f"[CHAT EXCEPTION] {e}")
        return {"reply": f"AI error: {e}"}

# ── ADMIN ──────────────────────────────────────────────────────────────────────
@app.post("/api/admin/keys")
async def get_keys(data: dict):
    if data.get("admin_pass") != ADMIN_PASSWORD: raise HTTPException(403, "Wrong password")
    return {"senior_key": ADMIN_SENIOR_KEY, "club_admin_key": CLUB_ADMIN_KEY}


# ═══════════════════════════════════════════════════════════════════════════════
# ── NEW FEATURES ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

# ── Models ────────────────────────────────────────────────────────────────────
class EventModel(BaseModel):
    title: str; club_id: str; description: str = ""
    event_date: str; event_time: str = ""
    location: str = "NIT Kurukshetra"; domain: Optional[str] = None

class ReviewModel(BaseModel):
    club_id: str; rating: int; liked: str = ""; improved: str = ""

class PollModel(BaseModel):
    title: str; body: str = ""; options: List[str]; tags: List[str] = []
    club_id: Optional[str] = None

# ── EVENTS CALENDAR ───────────────────────────────────────────────────────────
@app.post("/api/events")
async def create_event(d: EventModel, u=Depends(require_club_admin)):
    eid = str(ObjectId())
    club = await db.clubs.find_one({"_id": d.club_id})
    await db.events.insert_one({
        "_id": eid, "title": d.title, "club_id": d.club_id,
        "club_name": club["name"] if club else "", "club_icon": club.get("icon","🎯") if club else "🎯",
        "domain": d.domain or (club.get("domain","") if club else ""),
        "description": d.description, "event_date": d.event_date,
        "event_time": d.event_time, "location": d.location,
        "interested": [], "created_by": u["_id"],
        "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    })
    return clean(await db.events.find_one({"_id": eid}))

@app.get("/api/events")
async def get_events(domain: Optional[str]=None, u=Depends(optional_user)):
    q = {}
    if domain: q["domain"] = domain
    events = await db.events.find(q).to_list(200)
    events.sort(key=lambda e: e.get("event_date",""), reverse=False)
    uid = u["_id"] if u else None
    result = []
    for e in events:
        result.append({
            **clean(e),
            "interested_count": len(e.get("interested",[])),
            "is_interested": uid in e.get("interested",[]) if uid else False
        })
    return result

@app.post("/api/events/{event_id}/interested")
async def toggle_interested(event_id: str, u=Depends(current_user)):
    e = await db.events.find_one({"_id": event_id})
    if not e: raise HTTPException(404)
    uid = u["_id"]
    if uid in e.get("interested",[]):
        await db.events.update_one({"_id": event_id}, {"$pull": {"interested": uid}})
        return {"is_interested": False}
    else:
        await db.events.update_one({"_id": event_id}, {"$addToSet": {"interested": uid}})
        return {"is_interested": True}

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: str, u=Depends(require_club_admin)):
    await db.events.delete_one({"_id": event_id})
    return {"ok": True}

# ── ANONYMOUS POSTS ────────────────────────────────────────────────────────────


@app.post("/api/reviews")
async def create_review(d: ReviewModel, u=Depends(current_user)):
    if not u.get("email_verified"): raise HTTPException(403, "Email not verified")
    if not 1 <= d.rating <= 5: raise HTTPException(400, "Rating must be 1-5")
    club = await db.clubs.find_one({"_id": d.club_id})
    if not club: raise HTTPException(404, "Club not found")
    # Delete old review by same user
    await db.reviews.delete_one({"club_id": d.club_id, "user_id": u["_id"]})
    rid = str(ObjectId())
    await db.reviews.insert_one({
        "_id": rid, "club_id": d.club_id, "user_id": u["_id"],
        "rating": d.rating, "liked": d.liked, "improved": d.improved,
        "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    })
    # Update club avg_rating
    all_reviews = await db.reviews.find({"club_id": d.club_id}).to_list(500)
    avg = sum(r["rating"] for r in all_reviews) / len(all_reviews)
    await db.clubs.update_one({"_id": d.club_id}, {"$set": {"avg_rating": round(avg,1), "review_count": len(all_reviews)}})
    return {"ok": True, "avg_rating": round(avg,1)}

@app.get("/api/reviews/{club_id}")
async def get_reviews(club_id: str, u=Depends(optional_user)):
    reviews = await db.reviews.find({"club_id": club_id}).to_list(100)
    reviews.sort(key=lambda r: r.get("created_at",""), reverse=True)
    result = []
    for r in reviews:
        author = await db.users.find_one({"_id": r["user_id"]})
        result.append({
            "id": r["_id"], "rating": r["rating"],
            "liked": r.get("liked",""), "improved": r.get("improved",""),
            "created_at": r.get("created_at",""),
            "author": fmt_user(author) if author else {"name":"[deleted]","role":"student"},
            "is_mine": u and r["user_id"] == u["_id"]
        })
    return result

@app.delete("/api/reviews/{review_id}")
async def delete_review(review_id: str, u=Depends(current_user)):
    r = await db.reviews.find_one({"_id": review_id})
    if not r: raise HTTPException(404)
    if r["user_id"] != u["_id"] and u.get("role") not in ("club_admin","owner"):
        raise HTTPException(403)
    await db.reviews.delete_one({"_id": review_id})
    # Recalculate avg
    all_r = await db.reviews.find({"club_id": r["club_id"]}).to_list(500)
    avg = sum(x["rating"] for x in all_r) / len(all_r) if all_r else 0
    await db.clubs.update_one({"_id": r["club_id"]}, {"$set": {"avg_rating": round(avg,1) if avg else None, "review_count": len(all_r)}})
    return {"ok": True}

# ── POLLS ─────────────────────────────────────────────────────────────────────
@app.post("/api/polls")
async def create_poll(d: PollModel, u=Depends(current_user)):
    if not u.get("email_verified"): raise HTTPException(403)
    if len(d.options) < 2: raise HTTPException(400, "Need at least 2 options")
    pid = str(ObjectId())
    options_data = [{"text": opt, "votes": []} for opt in d.options]
    await db.polls.insert_one({
        "_id": pid, "title": d.title, "body": d.body,
        "options": options_data, "tags": d.tags, "club_id": d.club_id,
        "author_id": u["_id"], "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    })
    return await fmt_poll(await db.polls.find_one({"_id": pid}), u["_id"])

async def fmt_poll(poll, uid=None):
    author = await db.users.find_one({"_id": poll.get("author_id")})
    total = sum(len(o.get("votes",[])) for o in poll.get("options",[]))
    my_vote = None
    opts = []
    for i, o in enumerate(poll.get("options",[])):
        if uid and uid in o.get("votes",[]): my_vote = i
        opts.append({
            "text": o["text"],
            "votes": len(o.get("votes",[])),
            "pct": round(len(o.get("votes",[]))/total*100) if total else 0
        })
    return {
        "id": poll["_id"], "title": poll["title"], "body": poll.get("body",""),
        "options": opts, "total_votes": total, "my_vote": my_vote,
        "tags": poll.get("tags",[]), "club_id": poll.get("club_id"),
        "author": fmt_user(author) if author else {"name":"[deleted]","role":"student"},
        "created_at": poll.get("created_at","")
    }

@app.get("/api/polls")
async def get_polls(u=Depends(optional_user)):
    polls = await db.polls.find({}).to_list(100)
    polls.sort(key=lambda p: p.get("created_at",""), reverse=True)
    uid = u["_id"] if u else None
    return [await fmt_poll(p, uid) for p in polls]

@app.post("/api/polls/{poll_id}/vote/{option_idx}")
async def vote_poll(poll_id: str, option_idx: int, u=Depends(current_user)):
    p = await db.polls.find_one({"_id": poll_id})
    if not p: raise HTTPException(404)
    opts = p.get("options",[])
    if option_idx >= len(opts): raise HTTPException(400)
    # Remove any existing vote
    for i, o in enumerate(opts):
        if u["_id"] in o.get("votes",[]):
            await db.polls.update_one({"_id": poll_id}, {"$pull": {f"options.{i}.votes": u["_id"]}})
    # Add new vote
    await db.polls.update_one({"_id": poll_id}, {"$addToSet": {f"options.{option_idx}.votes": u["_id"]}})
    updated = await db.polls.find_one({"_id": poll_id})
    return await fmt_poll(updated, u["_id"])

@app.delete("/api/polls/{poll_id}")
async def delete_poll(poll_id: str, u=Depends(current_user)):
    p = await db.polls.find_one({"_id": poll_id})
    if not p: raise HTTPException(404)
    if p["author_id"] != u["_id"] and u.get("role") not in ("faculty_incharge","club_admin","owner"):
        raise HTTPException(403)
    await db.polls.delete_one({"_id": poll_id})
    return {"ok": True}

# ── PROFILE PAGE ──────────────────────────────────────────────────────────────
@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str, u=Depends(optional_user)):
    target = await db.users.find_one({"_id": user_id})
    if not target: raise HTTPException(404, "User not found")
    posts = await db.posts.find({"author_id": user_id, "anonymous": {"$ne": True}}).to_list(20)
    posts.sort(key=lambda p: p.get("created_at",""), reverse=True)
    return {
        "user": fmt_user(target),
        "bio": target.get("bio",""),
        "post_count": len(posts),
        "recent_posts": [{"id":p["_id"],"title":p["title"],"created_at":p.get("created_at","")} for p in posts[:5]],
        "is_me": u and u["_id"] == user_id
    }

@app.post("/api/auth/forgot-password")
async def forgot_password(data: dict):
    """Generate and store a password-reset OTP. In production, send via email service."""
    email = data.get("email", "").lower().strip()
    user = await db.users.find_one({"email": email})
    # Always return 200 to avoid user enumeration
    if not user:
        return {"message": "If this email is registered, you will receive an OTP shortly."}
    otp = gen_otp()
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
    await db.email_otps.update_one(
        {"email": email},
        {"$set": {"email": email, "otp": otp, "expires_at": expiry}},
        upsert=True
    )
    # In dev: log OTP to console. In production: send via email service.
    print(f"[FORGOT PASSWORD] OTP for {email}: {otp}")
    return {"message": "If this email is registered, you will receive an OTP shortly."}

# ── Password Reset ─────────────────────────────────────────────────────────
class ResetPasswordModel(BaseModel):
    email: str; otp: str; new_password: str

@app.post("/api/auth/reset-password")
async def reset_password(d: ResetPasswordModel):
    email = d.email.lower().strip()
    user  = await db.users.find_one({"email": email})
    if not user: raise HTTPException(404, "No account with this email")
    otp_doc = await db.email_otps.find_one({"email": email})
    if not otp_doc: raise HTTPException(400, "No OTP found. Request a new one.")
    if otp_doc["otp"] != d.otp: raise HTTPException(400, "Wrong OTP")
    from datetime import datetime
    if _safe_dt(otp_doc["expires_at"]) < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(400, "OTP expired. Request a new one.")
    if len(d.new_password) < 8: raise HTTPException(400, "Password must be at least 8 characters")
    pw_hash = bcrypt.hashpw(d.new_password.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({"email": email}, {"$set": {"password": pw_hash, "email_verified": True}})
    await db.email_otps.delete_one({"email": email})
    token = make_token(user["_id"], user["role"])
    return {"token": token, "user": fmt_user(await db.users.find_one({"_id": user["_id"]}))}

# ═══════════════════════════════════════════════════════════════════════════════
# ── OWNER: STAFF MANAGEMENT ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class CreateStaffModel(BaseModel):
    name: str
    email: str
    password: str
    role: str          # club_admin | faculty_incharge
    club_id: Optional[str] = None   # required when role=club_admin
    department: Optional[str] = ""  # for faculty

async def require_owner(u=Depends(current_user)):
    if u.get("role") not in ("owner", "club_admin", "faculty_incharge"):
        raise HTTPException(403, "Owner, Admin or Faculty access required")
    return u

@app.post("/api/owner/staff")
async def create_staff(d: CreateStaffModel, u=Depends(require_owner)):
    """Owner creates a club_admin or faculty_incharge account directly."""
    email = d.email.lower().strip()
    role  = d.role.lower()

    if u.get("role") == "club_admin":
        if role != "club_admin":
            raise HTTPException(403, "Club admins can only create other club admins")
        if not d.club_id or d.club_id != u.get("managed_club_id"):
            raise HTTPException(403, "You can only assign admins to your own club")
    
    if u.get("role") == "faculty_incharge":
        # Faculty can create club_admins for any club, or other faculty
        pass

    if role not in ("club_admin", "faculty_incharge"):
        raise HTTPException(400, "Role must be club_admin or faculty_incharge")
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")
    if len(d.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    pw_hash = bcrypt.hashpw(d.password.encode(), bcrypt.gensalt()).decode()
    uid = str(ObjectId())

    doc = {
        "_id": uid, "name": d.name, "email": email,
        "password": pw_hash, "role": role,
        "roll_number": "STAFF", "year": None, "branch": d.department or "",
        "email_verified": True, "verified": True,
        "bookmarks": [], "watchlist": [], "quiz_result": None,
        "bio": "", "department": d.department or "",
        "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
        "created_by_owner": True
    }

    if role == "club_admin" and d.club_id:
        doc["managed_club_id"] = d.club_id
        # Also tag the club with this admin
        await db.clubs.update_one({"_id": d.club_id}, {"$set": {"admin_id": uid}})

    await db.users.insert_one(doc)
    return {"message": "Staff account created!", "user": fmt_user(await db.users.find_one({"_id": uid}))}

@app.get("/api/owner/staff")
async def list_staff(u=Depends(require_owner)):
    """List all club_admin and faculty_incharge accounts."""
    staff = await db.users.find({
        "role": {"$in": ["club_admin", "faculty_incharge"]}
    }).to_list(200)
    
    if u.get("role") == "club_admin":
        staff = [s for s in staff if s.get("managed_club_id") == u.get("managed_club_id") and s.get("role") == "club_admin"]
    # Owners and FICs see all staff (owners see owner accounts too, but owners aren't in this list usually)
        
    result = []
    for s in staff:
        item = fmt_user(s)
        item["department"] = s.get("department", "")
        item["managed_club_id"] = s.get("managed_club_id", "")
        item["created_at"] = s.get("created_at", "")
        # Attach club name if club_admin
        if s.get("managed_club_id"):
            club = await db.clubs.find_one({"_id": s["managed_club_id"]})
            item["managed_club_name"] = club["name"] if club else "Unknown Club"
        else:
            item["managed_club_name"] = ""
        result.append(item)
    return result

@app.patch("/api/owner/staff/{user_id}/password")
async def reset_staff_password(user_id: str, data: dict, u=Depends(require_owner)):
    """Owner resets a staff member's password."""
    target = await db.users.find_one({"_id": user_id})
    if not target:
        raise HTTPException(404, "User not found")
    if u.get("role") == "club_admin":
        if target.get("role") != "club_admin" or target.get("managed_club_id") != u.get("managed_club_id"):
            raise HTTPException(403, "You can only manage admins from your own club")
            
    new_pw = data.get("password", "")
    if len(new_pw) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    pw_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({"_id": user_id}, {"$set": {"password": pw_hash}})
    return {"ok": True, "message": "Password updated"}

@app.patch("/api/owner/staff/{user_id}/club")
async def assign_club(user_id: str, data: dict, u=Depends(require_owner)):
    """Assign a club to a club_admin."""
    club_id = data.get("club_id", "")
    club = await db.clubs.find_one({"_id": club_id})
    if not club:
        raise HTTPException(404, "Club not found")
    await db.users.update_one({"_id": user_id}, {"$set": {"managed_club_id": club_id}})
    await db.clubs.update_one({"_id": club_id}, {"$set": {"admin_id": user_id}})
    return {"ok": True, "club_name": club["name"]}

@app.delete("/api/owner/staff/{user_id}")
async def delete_staff(user_id: str, u=Depends(require_owner)):
    """Owner removes a staff account."""
    target = await db.users.find_one({"_id": user_id})
    if not target:
        raise HTTPException(404, "User not found")
    if u.get("role") == "club_admin":
        if target.get("role") != "club_admin" or target.get("managed_club_id") != u.get("managed_club_id"):
            raise HTTPException(403, "You can only delete admins from your own club")
    if target.get("role") == "owner":
        raise HTTPException(403, "Cannot delete owner account")
    # Unassign from club
    if target.get("managed_club_id"):
        await db.clubs.update_one({"_id": target["managed_club_id"]}, {"$unset": {"admin_id": ""}})
    await db.users.delete_one({"_id": user_id})
    return {"ok": True}

@app.get("/api/owner/stats")
async def owner_stats(u=Depends(require_owner)):
    """Dashboard stats for owner."""
    return {
        "total_users":   await db.users.count_documents({}),
        "total_clubs":   await db.clubs.count_documents({}),
        "total_posts":   await db.posts.count_documents({}),
        "total_events":  await db.events.count_documents({}),
        "total_staff":   await db.users.count_documents({"role": {"$in": ["club_admin","faculty_incharge"]}}),
        "club_admins":   await db.users.count_documents({"role": "club_admin"}),
        "faculty":       await db.users.count_documents({"role": "faculty_incharge"}),
    }
