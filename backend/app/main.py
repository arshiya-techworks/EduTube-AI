import os, re, hmac, hashlib, base64, time, random, json
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func
from .db import Session, User, Video, WatchHistory, SavedVideo, ChatMessage, Note, QuizAttempt, Playlist, PlaylistVideo
from . import ai, rag, yt, demo

SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me").encode()
app = FastAPI(title="EduTube AI")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

def db():
    s = Session()
    try: yield s
    finally: s.close()
def hash_pw(p, salt=None):
    salt = salt or os.urandom(16).hex()
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", p.encode(), salt.encode(), 120000).hex()
def check_pw(p, h): return hmac.compare_digest(hash_pw(p, h.split("$")[0]), h)
def make_token(uid):
    body = f"{uid}:{int(time.time()) + 7 * 86400}"
    return base64.urlsafe_b64encode((body + ":" + hmac.new(SECRET, body.encode(), "sha256").hexdigest()).encode()).decode()
def parse_token(t):
    try:
        uid, exp, sig = base64.urlsafe_b64decode(t.encode()).decode().split(":")
        ok = hmac.compare_digest(sig, hmac.new(SECRET, f"{uid}:{exp}".encode(), "sha256").hexdigest())
        return int(uid) if ok and int(exp) > time.time() else None
    except Exception: return None
def user_opt(authorization: str = Header(None)):
    return parse_token(authorization.split()[-1]) if authorization else None
def user_req(uid=Depends(user_opt)):
    if not uid: raise HTTPException(401, "Please log in.")
    return uid

class Auth(BaseModel): email: str; password: str; name: str = ""
class Chat(BaseModel): message: str; video_id: str = ""; level: str = "Beginner"; history: list = []
class Quiz(BaseModel): video_id: str; n: int = 5
class Submit(BaseModel): video_id: str; answers: list  # [{topic, correct}]
class Save(BaseModel): video_id: str

@app.get("/api/health")
def health():
    p = ai.provider().name
    return {"ok": True, "demo_mode": p == "demo", "ai": p}

@app.post("/api/auth/register")
def register(a: Auth, s=Depends(db)):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", a.email) or len(a.password) < 6: raise HTTPException(400, "Enter a valid email and a password of 6+ characters.")
    if s.query(User).filter_by(email=a.email.lower()).first(): raise HTTPException(409, "Email already registered.")
    u = User(email=a.email.lower(), name=a.name or a.email.split("@")[0], password_hash=hash_pw(a.password)); s.add(u); s.commit()
    return {"token": make_token(u.id), "name": u.name}
@app.post("/api/auth/login")
def login(a: Auth, s=Depends(db)):
    u = s.query(User).filter_by(email=a.email.lower()).first()
    if not u or not check_pw(a.password, u.password_hash): raise HTTPException(401, "Invalid email or password.")
    return {"token": make_token(u.id), "name": u.name}
@app.post("/api/auth/logout")
def logout(): return {"ok": True}

def remember(s, v):
    if v.get("id") and not s.get(Video, v["id"]):
        s.add(Video(id=v["id"], title=v.get("title", ""), channel=v.get("channel", ""), thumbnail=v.get("thumbnail", ""), duration=v.get("duration", ""), views=v.get("views", ""))); s.commit()
@app.get("/api/videos/search")
def search(q: str = "", s=Depends(db)):
    if len(q) > 200: raise HTTPException(400, "Search is too long.")
    vids, is_demo = yt.search(q.strip())
    for v in vids: remember(s, v)
    return {"videos": vids, "demo_mode": is_demo}
@app.get("/api/videos/{vid}/transcript")
def transcript(vid: str):
    sec, src = yt.transcript(vid)
    return {"source": src, "sections": [{"topic": t, "text": x} for t, x in sec], "message": "" if sec else "Transcript unavailable for this video. The AI Teacher will use general knowledge."}
@app.get("/api/videos/{vid}")
def video(vid: str, s=Depends(db), uid=Depends(user_opt)):
    v = s.get(Video, vid) or next((Video(**{k: x[k] for k in ("id", "title", "channel", "thumbnail", "duration", "views")}) for x in demo.VIDEOS if x["id"] == vid), None)
    if not v: raise HTTPException(404, "Video not found.")
    if uid: remember(s, {"id": v.id, "title": v.title, "channel": v.channel, "thumbnail": v.thumbnail, "duration": v.duration, "views": v.views}); s.add(WatchHistory(user_id=uid, video_id=v.id)); s.commit()
    return {"id": v.id, "title": v.title, "channel": v.channel, "thumbnail": v.thumbnail, "duration": v.duration, "views": v.views}
@app.post("/api/videos/analyze")
def analyze(b: Save):
    m = re.search(r"(?:v=|youtu\.be/|embed/)([\w-]{11})", b.video_id); vid = m.group(1) if m else b.video_id
    sec, src = yt.transcript(vid); return {"video_id": vid, "chunks": len(rag.chunk(sec)), "source": src}

def ctx_for(vid, q, k=3):
    sec, _ = yt.transcript(vid); return rag.retrieve(rag.chunk(sec), q, k), sec
@app.post("/api/ai/chat")
def chat(b: Chat, s=Depends(db), uid=Depends(user_opt)):
    ctx, _ = ctx_for(b.video_id, b.message) if b.video_id else ([], [])
    v = s.get(Video, b.video_id) if b.video_id else None
    reply, prov = ai.answer(b.message, b.history, ctx, b.level, v.title if v else "General learning")
    if uid: s.add(ChatMessage(user_id=uid, video_id=b.video_id, role="user", content=b.message)); s.add(ChatMessage(user_id=uid, video_id=b.video_id, role="assistant", content=reply)); s.commit()
    return {"reply": reply, "provider": prov, "sources": [c["topic"] for c in ctx]}
@app.post("/api/ai/summary")
def summary(b: Chat):
    _, sec = ctx_for(b.video_id, "")
    if not sec: return {"summary": "Transcript unavailable, so a summary cannot be built."}
    return {"summary": "## Quick Summary\n" + "\n".join(f"- **{t}**: {x.split('.')[0]}." for t, x in sec) + "\n\n## Quick Revision\n" + "\n".join(f"- {t}" for t, _ in sec)}
@app.post("/api/ai/notes")
def notes(b: Chat, s=Depends(db), uid=Depends(user_opt)):
    _, sec = ctx_for(b.video_id, "")
    txt = "# Notes\n\n## Key Concepts\n" + "\n".join(f"- **{t}**: {x}" for t, x in sec) + "\n\n## Exam Points\n" + "\n".join(f"- Explain {t.lower()}." for t, _ in sec)
    if uid: s.add(Note(user_id=uid, video_id=b.video_id, content=txt)); s.commit()
    return {"notes": txt}
@app.post("/api/ai/explain")
def explain(b: Chat, s=Depends(db), uid=Depends(user_opt)): return chat(b, s, uid)

@app.post("/api/quiz/generate")
def quiz_generate(b: Quiz):
    """Cloze MCQs built from transcript sentences; each question is tagged with its topic."""
    _, sec = ctx_for(b.video_id, ""); pool = []
    llm = ai.make_quiz("this video", " ".join(f"{t}: {x}" for t, x in sec), b.n) if sec else None
    if llm: return {"questions": llm}
    for t, x in sec:
        for sent in re.split(r"(?<=[.!?])\s+", x):
            words = [w for w in re.findall(r"[A-Za-z]{6,}", sent)]
            if words: pool.append((t, sent, max(words, key=len)))
    if not pool: raise HTTPException(404, "Quiz unavailable: no transcript for this video.")
    allw = list({w for _, _, w in pool}); random.shuffle(pool); qs = []
    for t, sent, ans in pool[:b.n]:
        opts = random.sample([w for w in allw if w != ans], min(3, len(allw) - 1)) + [ans]; random.shuffle(opts)
        qs.append({"question": "Fill in the blank: " + sent.replace(ans, "_____", 1), "options": opts, "answer": ans, "topic": t, "explanation": f"From the section '{t}': {sent}"})
    return {"questions": qs}
@app.post("/api/quiz/submit")
def quiz_submit(b: Submit, s=Depends(db), uid=Depends(user_opt)):
    total = len(b.answers) or 1; score = sum(1 for a in b.answers if a.get("correct")); pct = round(100 * score / total)
    per = {}
    for a in b.answers: per.setdefault(a["topic"], []).append(bool(a.get("correct")))
    weak = [t for t, r in per.items() if sum(r) / len(r) < 0.5]; strong = [t for t, r in per.items() if sum(r) / len(r) >= 0.8]
    if uid: s.add(QuizAttempt(user_id=uid, video_id=b.video_id, score=score, total=total, weak=",".join(weak), strong=",".join(strong))); s.commit()
    return {"score": score, "total": total, "percentage": pct, "grade": "Excellent" if pct >= 80 else "Good" if pct >= 60 else "Needs Improvement",
            "weak": weak, "strong": strong, "recommendations": [f"Revise {t}" for t in weak] or ["Great work! Try another lesson."]}

@app.get("/api/dashboard")
def dashboard(s=Depends(db), uid=Depends(user_req)):
    att = s.query(QuizAttempt).filter_by(user_id=uid).all()
    avg = round(sum(100 * a.score / a.total for a in att) / len(att)) if att else 0
    weak = sorted({t for a in att for t in a.weak.split(",") if t})
    return {"videos_watched": s.query(func.count(func.distinct(WatchHistory.video_id))).filter(WatchHistory.user_id == uid).scalar(), "quiz_attempts": len(att), "average_score": avg, "weak_topics": weak,
            "strong_topics": sorted({t for a in att for t in a.strong.split(",") if t} - set(weak))}
@app.get("/api/history")
def history(s=Depends(db), uid=Depends(user_req)):
    rows = s.query(Video).join(WatchHistory, WatchHistory.video_id == Video.id).filter(WatchHistory.user_id == uid).order_by(WatchHistory.created.desc()).limit(30).all()
    return [{"id": v.id, "title": v.title, "channel": v.channel, "thumbnail": v.thumbnail} for v in rows]
@app.get("/api/watch-later")
def wl(s=Depends(db), uid=Depends(user_req)):
    rows = s.query(Video).join(SavedVideo, SavedVideo.video_id == Video.id).filter(SavedVideo.user_id == uid).all()
    return [{"id": v.id, "title": v.title, "channel": v.channel, "thumbnail": v.thumbnail} for v in rows]
@app.post("/api/watch-later")
def wl_add(b: Save, s=Depends(db), uid=Depends(user_req)):
    if not s.query(SavedVideo).filter_by(user_id=uid, video_id=b.video_id).first(): s.add(SavedVideo(user_id=uid, video_id=b.video_id)); s.commit()
    return {"ok": True}
@app.get("/api/learning-path")
def path(s=Depends(db), uid=Depends(user_req)):
    d = dashboard(s, uid); steps = [{"title": t, "status": "revise"} for t in d["weak_topics"]] + [{"title": t, "status": "done"} for t in d["strong_topics"]]
    return {"steps": steps, "completion": round(100 * len(d["strong_topics"]) / len(steps)) if steps else 0}

class PL(BaseModel): name: str = ""; video_id: str = ""
def _pl(s, uid, pid):
    p = s.query(Playlist).filter_by(id=pid, user_id=uid).first()
    if not p: raise HTTPException(404, "Playlist not found.")
    return p
@app.get("/api/playlists")
def pl_list(s=Depends(db), uid=Depends(user_req)):
    out = []
    for p in s.query(Playlist).filter_by(user_id=uid).all():
        vs = s.query(Video).join(PlaylistVideo, PlaylistVideo.video_id == Video.id).filter(PlaylistVideo.playlist_id == p.id).all()
        out.append({"id": p.id, "name": p.name, "videos": [{"id": v.id, "title": v.title, "channel": v.channel, "thumbnail": v.thumbnail} for v in vs]})
    return out
@app.post("/api/playlists")
def pl_create(b: PL, s=Depends(db), uid=Depends(user_req)):
    if not b.name.strip(): raise HTTPException(400, "Playlist name is required.")
    p = Playlist(user_id=uid, name=b.name.strip()[:80]); s.add(p); s.commit(); return {"id": p.id, "name": p.name}
@app.put("/api/playlists/{pid}")
def pl_rename(pid: int, b: PL, s=Depends(db), uid=Depends(user_req)):
    p = _pl(s, uid, pid); p.name = b.name.strip()[:80] or p.name; s.commit(); return {"id": p.id, "name": p.name}
@app.delete("/api/playlists/{pid}")
def pl_delete(pid: int, s=Depends(db), uid=Depends(user_req)):
    p = _pl(s, uid, pid); s.query(PlaylistVideo).filter_by(playlist_id=pid).delete(); s.delete(p); s.commit(); return {"ok": True}
@app.post("/api/playlists/{pid}/videos")
def pl_add(pid: int, b: PL, s=Depends(db), uid=Depends(user_req)):
    _pl(s, uid, pid)
    if not s.get(Video, b.video_id): raise HTTPException(404, "Open the video first.")
    if not s.query(PlaylistVideo).filter_by(playlist_id=pid, video_id=b.video_id).first(): s.add(PlaylistVideo(playlist_id=pid, video_id=b.video_id)); s.commit()
    return {"ok": True}
@app.delete("/api/playlists/{pid}/videos/{vid}")
def pl_remove(pid: int, vid: str, s=Depends(db), uid=Depends(user_req)):
    _pl(s, uid, pid); s.query(PlaylistVideo).filter_by(playlist_id=pid, video_id=vid).delete(); s.commit(); return {"ok": True}
@app.delete("/api/watch-later/{vid}")
def wl_remove(vid: str, s=Depends(db), uid=Depends(user_req)):
    s.query(SavedVideo).filter_by(user_id=uid, video_id=vid).delete(); s.commit(); return {"ok": True}
@app.delete("/api/history/{vid}")
def hist_remove(vid: str, s=Depends(db), uid=Depends(user_req)):
    s.query(WatchHistory).filter_by(user_id=uid, video_id=vid).delete(); s.commit(); return {"ok": True}

@app.post("/api/ai/exam")
def exam(b: Chat):
    _, sec = ctx_for(b.video_id, ""); return {"exam": ai.exam("this video", sec)}
@app.get("/api/dashboard/charts")
def charts(s=Depends(db), uid=Depends(user_req)):
    import datetime as dt
    today = dt.datetime.utcnow().date(); act = {today - dt.timedelta(days=i): 0 for i in range(6, -1, -1)}
    for (c,) in list(s.query(WatchHistory.created).filter(WatchHistory.user_id == uid)) + list(s.query(QuizAttempt.created).filter(QuizAttempt.user_id == uid)):
        if c.date() in act: act[c.date()] += 1
    tp = {}
    for a in s.query(QuizAttempt).filter_by(user_id=uid):
        for t in a.strong.split(","):
            if t: tp.setdefault(t, [0, 0])[0] += 1
        for t in a.weak.split(","):
            if t: tp.setdefault(t, [0, 0])[1] += 1
    return {"weekly": [{"day": d.strftime("%a"), "count": n} for d, n in act.items()],
            "topics": [{"topic": t, "percent": round(100 * g / (g + w))} for t, (g, w) in tp.items()],
            "quiz": [{"label": f"#{i+1}", "percent": round(100 * a.score / a.total)} for i, a in enumerate(s.query(QuizAttempt).filter_by(user_id=uid).order_by(QuizAttempt.id).limit(10))]}
@app.get("/api/notifications")
def notifications(s=Depends(db), uid=Depends(user_req)):
    d = dashboard(s, uid)
    return [f"Time to revise {t}." for t in d["weak_topics"]] + (["Take a quiz to start your learning path."] if not d["quiz_attempts"] else [])
class Prof(BaseModel): name: str = ""; level: str = "Beginner"; interests: str = ""
@app.get("/api/profile")
def profile(s=Depends(db), uid=Depends(user_req)):
    u = s.get(User, uid); d = dashboard(s, uid)
    return {"name": u.name, "email": u.email, "level": u.level, "interests": u.interests or "", "videos_watched": d["videos_watched"], "quiz_attempts": d["quiz_attempts"], "average_score": d["average_score"], "completed_topics": len(d["strong_topics"])}
@app.post("/api/profile")
def profile_save(b: Prof, s=Depends(db), uid=Depends(user_req)):
    u = s.get(User, uid); u.name = b.name.strip()[:60] or u.name; u.level = b.level if b.level in ("Beginner", "Intermediate", "Advanced") else u.level; u.interests = b.interests[:200]; s.commit()
    return {"ok": True, "name": u.name}
