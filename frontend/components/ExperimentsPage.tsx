"use client";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, CreatorSession, Experiment } from "@/lib/api";

export default function ExperimentsPage() {
  const [items, setItems] = useState<Experiment[]>([]);
  const [sessions, setSessions] = useState<CreatorSession[]>([]);
  const [name, setName] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [change, setChange] = useState("");
  const [sessionIds, setSessionIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setError("");
    try { const [experiments, creatorSessions] = await Promise.all([api.experiments(), api.sessions()]); setItems(experiments); setSessions(creatorSessions); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to load experiments."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await api.createExperiment({ name, hypothesis, change, outcome: "", session_ids: sessionIds }); setName(""); setHypothesis(""); setChange(""); setSessionIds([]); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Experiment could not be saved."); }
    finally { setBusy(false); }
  }
  async function transition(item: Experiment) {
    setBusy(true); setError("");
    try { if (item.status === "planned") await api.startExperiment(item.id); else await api.completeExperiment(item.id); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Experiment could not be updated."); }
    finally { setBusy(false); }
  }
  async function saveOutcome(item: Experiment, outcome: string) {
    setBusy(true); setError("");
    try { await api.updateExperiment(item.id, { outcome }); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Outcome could not be saved."); }
    finally { setBusy(false); }
  }
  if (loading) return <main className="workspace-loading"><p>Loading experiments…</p></main>;
  return <main className="experiments-page"><nav className="demo-nav"><Link href="/workspace">← Workspace</Link><span>OPSYRO · CREATOR EXPERIMENTS</span></nav><header className="experiments-heading"><p className="eyebrow">LEARN ACROSS SESSIONS</p><h1>Experiments</h1><p>Record a change, connect the sessions where you tried it, and capture what you learned.</p></header>
    {error && <p className="workspace-error" role="alert">{error} <button onClick={() => void load()}>Retry</button></p>}
    <section className="experiment-create"><h2>Plan an experiment</h2><form onSubmit={create}><label>Name<input required maxLength={120} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Pause for questions after each segment"/></label><label>What do you expect to learn?<textarea maxLength={500} value={hypothesis} onChange={e => setHypothesis(e.target.value)} rows={2}/></label><label>What will you change?<textarea maxLength={500} value={change} onChange={e => setChange(e.target.value)} rows={2}/></label><label>Related sessions<select multiple value={sessionIds.map(String)} onChange={e => setSessionIds(Array.from(e.target.selectedOptions, o => Number(o.value)))}>{sessions.map(s => <option key={s.id} value={s.id}>{s.title} · {s.status}</option>)}</select><small>Use Ctrl or Command to select more than one.</small></label><button disabled={busy}>Save experiment</button></form></section>
    <section className="experiment-list"><header><h2>Learning log</h2><span>{items.length} {items.length === 1 ? "experiment" : "experiments"}</span></header>{items.length === 0 ? <div className="experiment-empty"><h3>No experiments yet.</h3><p>Start with a small change in how you explain a moment or invite questions. Link a session when you have one to compare.</p></div> : items.map(item => <article className="experiment-row" key={item.id}><div className="experiment-main"><span className={`session-status status-${item.status === "complete" ? "ended" : item.status === "active" ? "live" : "draft"}`}>{item.status}</span><h3>{item.name}</h3><p>{item.hypothesis || "No hypothesis recorded."}</p>{item.change && <p><b>Change:</b> {item.change}</p>}<small>{item.session_ids.length} linked {item.session_ids.length === 1 ? "session" : "sessions"}{item.session_ids.length > 0 ? ` · ${item.session_ids.map(id => sessions.find(s => s.id === id)?.title || "Session").join(", ")}` : ""}</small></div><div className="experiment-outcome"><label htmlFor={`outcome-${item.id}`}>What happened?</label><textarea id={`outcome-${item.id}`} key={`${item.id}-${item.updated_at}`} defaultValue={item.outcome} maxLength={2000} rows={3} placeholder="Record what changed in the audience signals, recurring questions, or feedback."/><button disabled={busy} onClick={e => { const field = e.currentTarget.parentElement?.querySelector("textarea"); if (field) void saveOutcome(item, field.value); }}>Save note</button>{item.status !== "complete" && <button disabled={busy} onClick={() => void transition(item)}>{item.status === "planned" ? "Start" : "Complete"}</button>}</div></article>)}</section>
    <footer className="footerline"><Link href="/workspace">← Overview</Link><span>Notes are private to your creator account.</span></footer></main>;
}
