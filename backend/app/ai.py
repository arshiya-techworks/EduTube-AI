import os, re, json, urllib.request
UNAVAILABLE = "AI service is currently unavailable. Please check your API configuration."
LEVELS = {"Beginner": "Use simple language, analogies and steps.", "Intermediate": "Give technical explanations with examples.", "Advanced": "Give deep technical detail, equations and derivations."}
class DemoProvider:
    name = "demo"
    def chat(self, system, history, msg, ctx):
        if ctx:
            return "According to the video: " + " ".join(c["text"] for c in ctx[:2]) + "\n\nAdditional explanation (demo mode, no LLM connected): add an OpenAI key for richer, level-adapted answers."
        return "The video does not appear to cover this directly. I can explain it using general knowledge once an AI provider is configured (demo mode)."
class OpenAIProvider:
    name = "openai"
    def __init__(self, key): self.key = key
    def chat(self, system, history, msg, ctx):
        messages = [{"role": "system", "content": system}] + history[-10:] + [{"role": "user", "content": msg}]
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", json.dumps({"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": messages}).encode(),
                                     {"Content-Type": "application/json", "Authorization": "Bearer " + self.key})
        with urllib.request.urlopen(req, timeout=40) as r: return json.load(r)["choices"][0]["message"]["content"]

class OllamaProvider:
    name = "ollama"
    def __init__(self, model=None, host=None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
    def chat(self, system, history, msg, ctx):
        messages = [{"role": "system", "content": system}] + history[-10:] + [{"role": "user", "content": msg}]
        payload = {"model": self.model, "messages": messages, "stream": False}
        req = urllib.request.Request(self.host + "/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
        return data["message"]["content"]

def provider():
    # Prefer the free local Ollama model. OpenAI remains an optional fallback.
    try:
        p = OllamaProvider()
        req = urllib.request.Request(p.host + "/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as r:
            if r.status == 200:
                models = json.load(r).get("models", [])
                names = {m.get("name") for m in models}
                if p.model in names or any(n and n.split(":")[0] == p.model.split(":")[0] for n in names):
                    return p
    except Exception:
        pass
    k = os.getenv("OPENAI_API_KEY")
    return OpenAIProvider(k) if k else DemoProvider()

def answer(msg, history, ctx, level, title):
    p = provider()
    context = "\n".join(f"[{c['topic']}] {c['text']}" for c in ctx) or "(no relevant transcript found)"
    system = (f"You are EduTube AI Teacher for the video '{title}'. {LEVELS.get(level, '')} Use the transcript excerpts below. Prefix video-backed facts with 'According to the video:' and other material with 'Additional explanation:'. "
              f"Never attribute to the instructor anything absent from the excerpts. If the video doesn't cover it say: 'The video does not appear to cover this directly. I can explain it using general knowledge.'\n\nTRANSCRIPT EXCERPTS:\n{context}")
    try: return p.chat(system, history, msg, ctx), p.name
    except Exception: return UNAVAILABLE, "error"

def make_quiz(title, text, n):
    """LLM-written MCQs (OpenAI only). Returns None so callers can fall back to cloze questions."""
    p = provider()
    if p.name != "openai": return None
    prompt = (f"From this transcript of '{title}' write {n} multiple-choice questions as a JSON list of objects with keys question, options (4 strings), "
              f"answer (exactly one of the options), topic (short concept name), explanation. Output JSON only.\n\n{text[:6000]}")
    try:
        qs = json.loads(re.sub(r"```(?:json)?", "", p.chat("You output only valid JSON.", [], prompt, [])).strip())
        good = [q for q in qs if isinstance(q, dict) and len(q.get("options", [])) == 4 and q.get("answer") in q["options"] and q.get("question") and q.get("topic")]
        return [{k: q.get(k, "") for k in ("question", "options", "answer", "topic", "explanation")} for q in good[:n]] or None
    except Exception: return None
def exam(title, sections, level="Medium"):
    p = provider()
    if p.name == "openai":
        text = "\n".join(f"{t}: {x}" for t, x in sections)[:6000]
        try: return p.chat("You are an exam-setter.", [], f"For the video '{title}' write 3 short-answer, 2 long-answer, 3 viva and 2 interview questions (difficulty {level}) based on:\n{text}", [])
        except Exception: return UNAVAILABLE
    t = [x for x, _ in sections]
    if not t: return "Transcript unavailable, so exam questions cannot be built."
    return ("## Short-answer questions\n" + "\n".join(f"- Define {x.lower()}." for x in t) + "\n\n## Long-answer questions\n" + "\n".join(f"- Explain {x.lower()} with an example." for x in t[:2]) +
            "\n\n## Viva questions\n" + "\n".join(f"- Why is {x.lower()} important?" for x in t) + "\n\n## Interview questions\n" + "\n".join(f"- Where would you apply {x.lower()}?" for x in t[:3]) + "\n\n(Demo mode: add an OpenAI key for richer questions.)")
