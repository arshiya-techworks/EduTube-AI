import re, math
from collections import Counter
def chunk(sections, size=60, overlap=15):
    """sections: [(topic, text)] -> chunks with word windows (size/overlap in words)."""
    out = []
    for topic, text in sections:
        w = text.split(); i = 0
        while i < len(w):
            out.append({"topic": topic, "text": " ".join(w[i:i + size])})
            if i + size >= len(w): break
            i += size - overlap
    return out
def _vec(t): return Counter(re.findall(r"[a-z0-9]{3,}", t.lower()))
def _cos(a, b):
    d = sum(a[k] * b.get(k, 0) for k in a)
    n = math.sqrt(sum(x * x for x in a.values())) * math.sqrt(sum(x * x for x in b.values()))
    return d / n if n else 0.0
def retrieve(chunks, query, k=3):
    q = _vec(query)
    scored = sorted(((_cos(q, _vec(c["topic"] + " " + c["text"])), c) for c in chunks), key=lambda x: -x[0])
    return [dict(c, score=s) for s, c in scored[:k] if s > 0.05]
