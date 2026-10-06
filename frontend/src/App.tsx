import { useEffect, useState } from "react";
import { Search, Moon, Sun, GraduationCap, Send } from "lucide-react";

type Video = { id: string; title: string; channel: string; thumbnail: string; duration: string; views: string; difficulty?: string };
type Msg = { role: "user" | "assistant"; content: string };
type Q = { question: string; options: string[]; answer: string; topic: string; explanation: string };
type Result = { percentage: number; grade: string; weak: string[]; strong: string[]; recommendations: string[] };

async function api<T>(path: string, body?: unknown): Promise<T> {
  const token = localStorage.getItem("token");
  try {
    const r = await fetch("/api" + path, { method: body ? "POST" : "GET", headers: { "Content-Type": "application/json", ...(token ? { Authorization: "Bearer " + token } : {}) }, body: body ? JSON.stringify(body) : undefined });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "Something went wrong.");
    return d;
  } catch (e) { throw new Error(e instanceof Error && e.message !== "Failed to fetch" ? e.message : "Cannot reach the server. Please try again."); }
}
const TOPICS = ["Python", "SQL", "Machine Learning", "Thermodynamics", "Data Science", "Java"];

export default function App() {
  const [dark, setDark] = useState(localStorage.getItem("dark") === "1");
  const [view, setView] = useState<"home" | "watch" | "dash" | "list" | "auth" | "pl" | "profile" | "notif">("home");
  const [videos, setVideos] = useState<Video[]>([]);
  const [demo, setDemo] = useState(false);
  const [loading, setLoading] = useState("");
  const [toast, setToast] = useState("");
  const [q, setQ] = useState("");
  const [video, setVideo] = useState<Video | null>(null);
  const [level, setLevel] = useState("Beginner");
  const [user, setUser] = useState(localStorage.getItem("name") || "");
  const [list, setList] = useState<{ title: string; items: Video[] }>({ title: "", items: [] });
  const [dash, setDash] = useState<any>(null);
  const [prof, setProf] = useState<any>(null);
  const [notes, setNotes] = useState<string[]>([]);
  const [charts, setCharts] = useState<any>(null);
  const [path, setPath] = useState<{ title: string; status: string }[]>([]);
  const [pls, setPls] = useState<{ id: number; name: string; videos: Video[] }[]>([]);
  const loadPl = () => run("Loading...", async () => { setPls(await api("/playlists")); setView("pl"); });
  const say = (m: string) => { setToast(m); setTimeout(() => setToast(""), 3000); };
  useEffect(() => { document.documentElement.className = dark ? "dark" : ""; localStorage.setItem("dark", dark ? "1" : "0"); }, [dark]);
  const run = async (label: string, f: () => Promise<void>) => { setLoading(label); try { await f(); } catch (e) { say((e as Error).message); } setLoading(""); };
  const search = (term: string) => run("Searching educational videos...", async () => {
    setQ(term); const r = await api<{ videos: Video[]; demo_mode: boolean }>("/videos/search?q=" + encodeURIComponent(term));
    setVideos(r.videos); setDemo(r.demo_mode); setView("home");
  });
  const open = (v: Video) => { setVideo(v); setView("watch"); api("/videos/" + v.id).catch(() => undefined); };
  const show = (title: string, path: string) => run("Loading...", async () => { setList({ title, items: await api<Video[]>(path) }); setView("list"); });
  const openUrl = () => { const u = prompt("Paste a YouTube URL"); const m = u?.match(/(?:v=|youtu\.be\/|embed\/)([\w-]{11})/); if (m) open({ id: m[1], title: "YouTube video", channel: "", thumbnail: "", duration: "", views: "" }); else if (u) say("That does not look like a YouTube URL."); };
  const logout = () => { localStorage.clear(); setUser(""); say("Logged out"); };

  return (<div>
    <div className="nav">
      <div className="logo" onClick={() => setView("home")}><img src="/logo.svg" alt="" />EduTube AI</div>
      <form className="search" onSubmit={e => { e.preventDefault(); search(q); }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search videos, courses and topics..." /><button><Search size={18} /></button></form>
      <button className="btn" onClick={() => show("History", "/history")}>History</button>
      <button className="btn" onClick={() => show("Watch Later", "/watch-later")}>Watch Later</button>
      <button className="btn" onClick={() => run("Loading...", async () => { setDash(await api("/dashboard")); setCharts(await api("/dashboard/charts")); setPath((await api<{ steps: { title: string; status: string }[] }>("/learning-path")).steps); setView("dash"); })}>My Learning</button>
      <button className="btn" onClick={() => search("Machine Learning")}>Trending</button>
      <button className="btn" onClick={loadPl}>Playlists</button>
      <button className="btn" onClick={openUrl}>Open YouTube URL</button>
      <button className="btn" style={{ display: "none" }} onClick={openUrl}>Open YouTube URL</button>
      <button className="btn" onClick={() => run("Loading...", async () => { setNotes(await api("/notifications")); setView("notif"); })}>🔔</button>
      <button className="btn" onClick={() => setDark(!dark)}>{dark ? <Sun size={16} /> : <Moon size={16} />}</button>
      {user ? <><button className="btn" onClick={() => run("Loading...", async () => { setProf(await api("/profile")); setView("profile"); })}>👤 {user}</button><button className="btn" onClick={logout}>Logout</button></> : <button className="btn pri" onClick={() => setView("auth")}>Login / Register</button>}
    </div>
    <div className="wrap">
      {loading && <p className="mut">{loading}</p>}
      {view === "home" && <>
        {!videos.length && <div className="hero"><GraduationCap size={40} /><h1>Learn anything. Smarter.</h1><p>Watch educational videos, ask questions, practice and master every topic with AI.</p>
          <p><b>Watch. Learn. Ask. Master.</b></p><div className="chips">{TOPICS.map(t => <button key={t} className="chip" onClick={() => search(t)}>{t}</button>)}</div></div>}
        {demo && videos.length > 0 && <p><span className="badge">Demo Mode</span> <span className="mut">Sample videos shown. Add YOUTUBE_API_KEY for live search.</span></p>}
        {loading ? <div className="grid">{[1, 2, 3, 4].map(i => <div key={i} className="skel" />)}</div> : <Grid items={videos} open={open} />}
      </>}
      {view === "list" && <><h2>{list.title}</h2>{list.items.length ? <Grid items={list.items} open={open} /> : <p className="mut">Nothing here yet. Log in and watch a video to fill this page.</p>}</>}
      {view === "auth" && <Auth done={n => { setUser(n); setView("home"); say("Welcome, " + n); }} />}
      {view === "dash" && dash && <div className="grid">
        {[["Videos Watched", dash.videos_watched], ["Quiz Attempts", dash.quiz_attempts], ["Average Score", dash.average_score + "%"], ["Strong Topics", dash.strong_topics.join(", ") || "-"], ["Weak Topics", dash.weak_topics.join(", ") || "-"]].map(([k, v]) =>
          <div className="panel" key={k as string}><small className="mut">{k}</small><h2>{v}</h2></div>)}
        <div className="panel" style={{ gridColumn: "1/-1" }}><b>My Learning Path</b>{!path.length && <p className="mut">Take a quiz to build your path.</p>}
          {path.map(x => <p key={x.title}>{x.status === "done" ? "✓" : "→"} {x.title} <span className="mut">({x.status === "done" ? "strong" : "revise"})</span></p>)}
          {charts && <><Bars title="Weekly Learning Activity" rows={charts.weekly.map((x: any) => ({ l: x.day, v: x.count }))} max={Math.max(1, ...charts.weekly.map((x: any) => x.count))} />
            <Bars title="Quiz Performance (%)" rows={charts.quiz.map((x: any) => ({ l: x.label, v: x.percent }))} max={100} />
            <Bars title="Topic Performance (%)" rows={charts.topics.map((x: any) => ({ l: x.topic.slice(0, 8), v: x.percent }))} max={100} /></>}
          <div style={{ background: "var(--bd)", borderRadius: 8, height: 12 }}><div style={{ width: dash.average_score + "%", background: "var(--pri)", height: 12, borderRadius: 8 }} /></div><small className="mut">Average quiz score</small></div></div>}
      {view === "pl" && <div><button className="btn pri" onClick={async () => { const n = prompt("Playlist name"); if (n) { try { await api("/playlists", { name: n }); loadPl(); } catch (e) { say((e as Error).message); } } }}>+ New playlist</button>
        {!pls.length && <p className="mut">No playlists yet. Log in and create one.</p>}
        {pls.map(p => <div key={p.id} className="panel" style={{ margin: "14px 0" }}><b>{p.name}</b> <button className="btn" onClick={async () => { const n = prompt("New name", p.name); if (n) { await fetch("/api/playlists/" + p.id, { method: "PUT", headers: { "Content-Type": "application/json", Authorization: "Bearer " + localStorage.getItem("token") }, body: JSON.stringify({ name: n }) }); loadPl(); } }}>Rename</button> <button className="btn" onClick={async () => { await fetch("/api/playlists/" + p.id, { method: "DELETE", headers: { Authorization: "Bearer " + localStorage.getItem("token") } }); loadPl(); }}>Delete</button>
          <Grid items={p.videos} open={open} /></div>)}</div>}
      {view === "notif" && <div className="panel"><h2>Notifications</h2>{notes.length ? notes.map(n => <p key={n}>🔔 {n}</p>) : <p className="mut">You're all caught up. Log in to get revision reminders.</p>}</div>}
      {view === "profile" && prof && <div className="panel" style={{ maxWidth: 440, margin: "20px auto" }}><h2>Profile</h2><p className="mut">{prof.email}</p>
        <input className="btn" style={{ width: "100%", margin: 4 }} value={prof.name} onChange={e => setProf({ ...prof, name: e.target.value })} placeholder="Name" />
        <select className="btn" style={{ width: "100%", margin: 4 }} value={prof.level} onChange={e => { setProf({ ...prof, level: e.target.value }); setLevel(e.target.value); }}>{["Beginner", "Intermediate", "Advanced"].map(l => <option key={l}>{l}</option>)}</select>
        <input className="btn" style={{ width: "100%", margin: 4 }} value={prof.interests} onChange={e => setProf({ ...prof, interests: e.target.value })} placeholder="Interests (e.g. SQL, Thermodynamics)" />
        <button className="btn pri" onClick={async () => { try { const r = await api<{ name: string }>("/profile", prof); localStorage.setItem("name", r.name); setUser(r.name); say("Profile saved"); } catch (e) { say((e as Error).message); } }}>Save</button>
        <p>Videos watched: <b>{prof.videos_watched}</b> · Quiz attempts: <b>{prof.quiz_attempts}</b> · Avg score: <b>{prof.average_score}%</b> · Completed topics: <b>{prof.completed_topics}</b></p></div>}
      {view === "watch" && video && <Watch video={video} level={level} setLevel={setLevel} say={say} />}
    </div>
    {toast && <div className="toast">{toast}</div>}
  </div>);
}

function Bars({ title, rows, max }: { title: string; rows: { l: string; v: number }[]; max: number }) {
  return <div style={{ margin: "16px 0" }}><b>{title}</b>{!rows.length && <p className="mut">No data yet.</p>}
    <div style={{ display: "flex", gap: 8, alignItems: "flex-end", height: 110 }}>{rows.map(r => <div key={r.l} style={{ flex: 1, textAlign: "center", fontSize: 11 }}>{r.v}<div style={{ height: Math.max(2, (90 * r.v) / max), background: "var(--pri)", borderRadius: 4 }} />{r.l}</div>)}</div></div>;
}

function Grid({ items, open }: { items: Video[]; open: (v: Video) => void }) {
  return <div className="grid">{items.map(v => <div className="vcard" key={v.id} onClick={() => open(v)}><img src={v.thumbnail} alt="" />
    <div><b>{v.title}</b><br /><small>{v.channel}</small><br /><small>{v.views} · {v.duration} {v.difficulty && "· " + v.difficulty}</small></div></div>)}</div>;
}

function Auth({ done }: { done: (n: string) => void }) {
  const [f, setF] = useState({ email: "", password: "", name: "" }); const [reg, setReg] = useState(false); const [err, setErr] = useState("");
  const go = async () => { try { const r = await api<{ token: string; name: string }>(reg ? "/auth/register" : "/auth/login", f); localStorage.setItem("token", r.token); localStorage.setItem("name", r.name); done(r.name); } catch (e) { setErr((e as Error).message); } };
  return <div className="panel" style={{ maxWidth: 380, margin: "40px auto" }}><h2>{reg ? "Create account" : "Login"}</h2>
    {reg && <input className="btn" style={{ width: "100%", margin: 4 }} placeholder="Name" value={f.name} onChange={e => setF({ ...f, name: e.target.value })} />}
    <input className="btn" style={{ width: "100%", margin: 4 }} placeholder="Email" value={f.email} onChange={e => setF({ ...f, email: e.target.value })} />
    <input className="btn" style={{ width: "100%", margin: 4 }} type="password" placeholder="Password" value={f.password} onChange={e => setF({ ...f, password: e.target.value })} />
    {err && <p style={{ color: "#dc2626" }}>{err}</p>}<button className="btn pri" onClick={go}>{reg ? "Register" : "Login"}</button>{" "}
    <button className="btn" onClick={() => setReg(!reg)}>{reg ? "Have an account?" : "New here?"}</button></div>;
}

function Watch({ video, level, setLevel, say }: { video: Video; level: string; setLevel: (l: string) => void; say: (m: string) => void }) {
  const [tab, setTab] = useState("Overview"); const [text, setText] = useState(""); const [msgs, setMsgs] = useState<Msg[]>([]); const [input, setInput] = useState(""); const [busy, setBusy] = useState(false);
  const [qs, setQs] = useState<Q[]>([]); const [picked, setPicked] = useState<Record<number, string>>({}); const [res, setRes] = useState<Result | null>(null); const [open, setOpen] = useState(true);
  const send = async (m: string) => {
    if (!m.trim()) return; const history = msgs.slice(-10); setMsgs(x => [...x, { role: "user", content: m }]); setInput(""); setBusy(true);
    try { const r = await api<{ reply: string }>("/ai/chat", { message: m, video_id: video.id, level, history }); setMsgs(x => [...x, { role: "assistant", content: r.reply }]); }
    catch (e) { setMsgs(x => [...x, { role: "assistant", content: "AI Teacher is temporarily unavailable. Please check your AI configuration." }]); }
    setBusy(false);
  };
  const load = async (t: string) => {
    setTab(t); setText("Loading...");
    try {
      if (t === "Transcript") { const r = await api<{ sections: { topic: string; text: string }[]; message: string }>(`/videos/${video.id}/transcript`); setText(r.sections.map(s => `${s.topic}\n${s.text}`).join("\n\n") || r.message); }
      else if (t === "Exam Prep") setText((await api<{ exam: string }>("/ai/exam", { video_id: video.id, message: "" })).exam);
      else if (t === "Summary") setText((await api<{ summary: string }>("/ai/summary", { video_id: video.id })).summary);
      else if (t === "Smart Notes") setText((await api<{ notes: string }>("/ai/notes", { video_id: video.id })).notes);
      else if (t === "Quiz") { setQs((await api<{ questions: Q[] }>("/quiz/generate", { video_id: video.id, n: 5 })).questions); setPicked({}); setRes(null); setText(""); }
      else setText(video.title + " by " + video.channel);
    } catch (e) { setText((e as Error).message); }
  };
  useEffect(() => { load("Overview"); setMsgs([]); }, [video.id]);
  const submit = async () => setRes(await api<Result>("/quiz/submit", { video_id: video.id, answers: qs.map((q, i) => ({ topic: q.topic, correct: picked[i] === q.answer })) }));
  const modes: [string, string][] = [["💡 Explain", "Explain the main idea of this video simply."], ["📝 Summarize", "Summarize this video."], ["🌎 Example", "Give me a real-world example."], ["🏭 Application", "Where is this used in practice?"], ["🎯 Exam", "Create 3 exam questions on this video."], ["🔬 Advanced", "Give an advanced explanation."]];
  return <div className="watch"><div>
    <iframe className="player" src={`https://www.youtube.com/embed/${video.id}`} title={video.title} allow="accelerometer; autoplay; encrypted-media; picture-in-picture" allowFullScreen />
    <h2>{video.title}</h2><p className="mut">{video.channel}</p>
    <div className="row"><button className="btn" onClick={() => api("/watch-later", { video_id: video.id }).then(() => say("Saved to Watch Later")).catch(e => say(e.message))}>Watch Later</button>
      <button className="btn" onClick={async () => { try { const l = await api<{ id: number; name: string }[]>("/playlists"); if (!l.length) return say("Create a playlist first."); const n = prompt("Add to which playlist?\n" + l.map(x => x.name).join(", ")); const t = l.find(x => x.name === n); if (t) { await api(`/playlists/${t.id}/videos`, { video_id: video.id }); say("Added to " + t.name); } } catch (e) { say((e as Error).message); } }}>Add to Playlist</button>
      <button className="btn" onClick={() => { navigator.clipboard?.writeText(`https://youtu.be/${video.id}`); say("Link copied"); }}>Share</button>
      {["Beginner", "Intermediate", "Advanced"].map(l => <button key={l} className={"btn" + (level === l ? " pri" : "")} onClick={() => setLevel(l)}>{l}</button>)}</div>
    <div className="tabs">{["Overview", "Transcript", "Smart Notes", "Summary", "Exam Prep", "Quiz"].map(t => <button key={t} className={"btn" + (tab === t ? " on" : "")} onClick={() => load(t)}>{t}</button>)}</div>
    {tab !== "Quiz" && <div className="panel" style={{ whiteSpace: "pre-wrap" }}>{text}{tab === "Smart Notes" && text.startsWith("#") && <div className="row"><button className="btn" onClick={() => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text])); a.download = "notes.md"; a.click(); }}>Download</button></div>}</div>}
    {tab === "Quiz" && <div className="panel">{qs.map((q, i) => <div key={i}><b>{i + 1}. {q.question}</b>{q.options.map(o => <button key={o} disabled={!!res} className={"btn opt" + (res ? (o === q.answer ? " ok" : picked[i] === o ? " bad" : "") : picked[i] === o ? " on" : "")} onClick={() => setPicked({ ...picked, [i]: o })}>{o}</button>)}{res && <p className="mut">{q.explanation}</p>}</div>)}
      {qs.length > 0 && !res && <button className="btn pri" onClick={submit}>Submit quiz</button>}
      {res && <div><h3>{res.percentage}% · {res.grade}</h3><p>Weak: {res.weak.join(", ") || "none"} · Strong: {res.strong.join(", ") || "none"}</p>{res.recommendations.map(r => <p key={r}>→ {r}</p>)}<button className="btn" onClick={() => load("Quiz")}>Retake</button></div>}</div>}
  </div>
  {open ? <div className="panel chat"><b>🤖 EduTube AI Teacher</b><div className="row">{modes.map(([l, p]) => <button key={l} className="chip" onClick={() => send(p)}>{l}</button>)}<button className="chip" onClick={() => { setTab("Quiz"); load("Quiz"); }}>🧠 Quiz Me</button></div>
    <div className="msgs">{!msgs.length && <p className="mut">Ask anything about this video...</p>}{msgs.map((m, i) => <div key={i} className={"m " + m.role}>{m.content}</div>)}{busy && <p className="mut">Preparing answer...</p>}</div>
    <div className="search"><input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send(input)} placeholder="Ask anything about this video..." /><button onClick={() => send(input)}><Send size={16} /></button></div></div>
    : <button className="fab" onClick={() => setOpen(true)}>🤖</button>}</div>;
}
