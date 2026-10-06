import os, json, re, urllib.request, urllib.parse
from . import demo
def _get(url):
    with urllib.request.urlopen(url, timeout=10) as r: return json.load(r)
def _dur(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or ""); h, mi, s = [int(x or 0) for x in m.groups()] if m else (0, 0, 0)
    return f"{h}:{mi:02d}:{s:02d}" if h else f"{mi}:{s:02d}"
def search(q):
    """Returns (videos, demo_mode). Falls back to demo videos on any failure."""
    key = os.getenv("YOUTUBE_API_KEY")
    if key:
        try:
            p = urllib.parse.urlencode({"part": "snippet", "q": q + " tutorial", "type": "video", "videoEmbeddable": "true", "maxResults": 12, "key": key})
            items = _get("https://www.googleapis.com/youtube/v3/search?" + p)["items"]
            ids = ",".join(i["id"]["videoId"] for i in items)
            det = {d["id"]: d for d in _get("https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode({"part": "contentDetails,statistics", "id": ids, "key": key}))["items"]}
            out = [{"id": i["id"]["videoId"], "title": i["snippet"]["title"], "channel": i["snippet"]["channelTitle"], "thumbnail": i["snippet"]["thumbnails"]["high"]["url"],
                    "duration": _dur(det.get(i["id"]["videoId"], {}).get("contentDetails", {}).get("duration")), "views": f"{int(det.get(i['id']['videoId'], {}).get('statistics', {}).get('viewCount', 0)):,} views",
                    "published": i["snippet"]["publishedAt"][:10], "difficulty": ""} for i in items]
            if out: return out, False
        except Exception: pass
    return demo.search(q), True
_cache = {}
def transcript(vid):
    """Returns (sections, source). Never raises. Supports youtube-transcript-api 0.x and 1.x."""
    if vid in demo.TRANSCRIPTS: return demo.TRANSCRIPTS[vid], "demo"
    if vid in _cache: return _cache[vid], "youtube"
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        if hasattr(YouTubeTranscriptApi, "get_transcript"): texts = [x["text"] for x in YouTubeTranscriptApi.get_transcript(vid)]
        else: texts = [x.text for x in YouTubeTranscriptApi().fetch(vid)]
        texts = [t.replace("\n", " ") for t in texts]
        out = [(f"Segment {i // 12 + 1}", " ".join(texts[i:i + 12])) for i in range(0, len(texts), 12)]
        if out: _cache[vid] = out; return out, "youtube"
    except Exception: pass
    return [], "unavailable"
