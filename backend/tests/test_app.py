import os, sys, tempfile
os.environ["EDUTUBE_NO_DOTENV"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "t.db")
os.environ.pop("OPENAI_API_KEY", None); os.environ.pop("YOUTUBE_API_KEY", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from app.main import app
from app import rag
c = TestClient(app); V = "rfscVS0vtbw"
def test_auth_and_dashboard():
    t = c.post("/api/auth/register", json={"email": "a@b.co", "password": "secret1"}).json()["token"]
    assert c.post("/api/auth/login", json={"email": "a@b.co", "password": "bad"}).status_code == 401
    assert c.post("/api/auth/login", json={"email": "a@b.co", "password": "secret1"}).status_code == 200
    h = {"Authorization": "Bearer " + t}
    c.get(f"/api/videos/{V}", headers=h)
    qs = c.post("/api/quiz/generate", json={"video_id": V}).json()["questions"]
    r = c.post("/api/quiz/submit", headers=h, json={"video_id": V, "answers": [{"topic": q["topic"], "correct": False} for q in qs]}).json()
    assert r["grade"] == "Needs Improvement" and r["weak"]
    d = c.get("/api/dashboard", headers=h).json(); assert d["quiz_attempts"] == 1 and d["videos_watched"] == 1
    assert c.get("/api/learning-path", headers=h).json()["steps"]
def test_search_transcript_rag_chat():
    r = c.get("/api/videos/search?q=python functions").json(); assert r["demo_mode"] and r["videos"]
    assert c.get(f"/api/videos/{V}/transcript").json()["sections"]
    assert rag.retrieve(rag.chunk([("A", "return statement sends value back")]), "return value")
    a = c.post("/api/ai/chat", json={"message": "What is a parameter?", "video_id": V}).json()["reply"]; assert "According to the video" in a
    assert "does not appear to cover" in c.post("/api/ai/chat", json={"message": "quantum chromodynamics", "video_id": V}).json()["reply"]
def test_playlists_and_lists():
    t = c.post("/api/auth/register", json={"email": "p@b.co", "password": "secret1"}).json()["token"]; h = {"Authorization": "Bearer " + t}
    c.get(f"/api/videos/{V}", headers=h)
    pid = c.post("/api/playlists", headers=h, json={"name": "Python"}).json()["id"]
    assert c.post(f"/api/playlists/{pid}/videos", headers=h, json={"video_id": V}).status_code == 200
    assert c.get("/api/playlists", headers=h).json()[0]["videos"]
    assert c.put(f"/api/playlists/{pid}", headers=h, json={"name": "Py2"}).json()["name"] == "Py2"
    assert c.delete(f"/api/playlists/{pid}", headers=h).status_code == 200
    c.post("/api/watch-later", headers=h, json={"video_id": V}); assert c.delete(f"/api/watch-later/{V}", headers=h).status_code == 200
    assert c.get("/api/history", headers=h).json()
    assert c.get("/api/dashboard").status_code == 401

def test_exam_profile_charts():
    t = c.post("/api/auth/register", json={"email": "q@b.co", "password": "secret1"}).json()["token"]; h = {"Authorization": "Bearer " + t}
    assert "Viva" in c.post("/api/ai/exam", json={"message": "", "video_id": V}).json()["exam"]
    assert c.post("/api/profile", headers=h, json={"name": "Sam", "level": "Advanced", "interests": "SQL"}).json()["name"] == "Sam"
    assert c.get("/api/profile", headers=h).json()["level"] == "Advanced"
    assert len(c.get("/api/dashboard/charts", headers=h).json()["weekly"]) == 7
    assert isinstance(c.get("/api/notifications", headers=h).json(), list)
