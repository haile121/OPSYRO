"use client";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, Creator, CreatorSession } from "@/lib/api";

export default function CreatorWorkspace() {
  const [creator, setCreator] = useState<Creator | null>(null);
  const [sessions, setSessions] = useState<CreatorSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [unauthorized, setUnauthorized] = useState(false);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [twitchChannelId, setTwitchChannelId] = useState("");
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const user = await api.me(); setCreator(user); setUnauthorized(false);
      setSessions(await api.sessions());
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "Unable to load workspace.";
      if (message.includes("Authentication credentials")) setUnauthorized(true);
      else setError(message);
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try { await api.createSession({ title, description, twitch_channel_id: twitchChannelId }); setTitle(""); setDescription(""); setTwitchChannelId(""); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Session could not be saved."); }
    finally { setBusy(false); }
  }
  async function transition(session: CreatorSession, action: "start" | "end") {
    setBusy(true); setError("");
    try { action === "start" ? await api.startSession(session.id) : await api.endSession(session.id); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Session could not be updated."); }
    finally { setBusy(false); }
  }
  async function signOut() { try { await api.logout(); window.location.assign("/"); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not sign out."); } }
  if (loading) return <main className="workspace-loading"><p>Loading your workspace…</p></main>;
  if (unauthorized) return <main className="workspace-loading"><p className="eyebrow">CREATOR WORKSPACE</p><h1>Sign in to see your sessions.</h1><Link className="primary-action" href="/sign-in">Sign in ↗</Link><p>New creator? <Link href="/register">Create an account</Link></p></main>;
  return <div className="workspace"><aside className="sidebar" aria-label="Workspace navigation"><Link className="brand" href="/">◢ OPSYRO</Link><p className="nav-label">Workspace</p><nav><a className="nav-item" href="#sessions" aria-current="page">◦ Overview</a><a className="nav-item" href="#sessions">▱ Live sessions</a><Link className="nav-item" href="/workspace/experiments">◌ Experiments</Link></nav><p className="sidebar-note">Audience curiosity, made visible.<br/>Twitch is not connected</p></aside><main className="main"><header className="topline"><div><p className="eyebrow">Creator workspace</p><h1>Overview</h1></div><div className="creator-controls"><span>{creator?.username}</span><button onClick={signOut}>Sign out</button></div></header><section className="workspace-welcome"><div><p className="eyebrow">YOUR SESSIONS</p><h2>Bring curiosity into view.</h2><p>Create a session to prepare a place for audience questions and attention signals.</p></div><span className="session-count">{sessions.length.toString().padStart(2,"0")}<small>sessions</small></span></section>
    {error && <p className="workspace-error" role="alert">{error} <button onClick={() => void load()}>Retry</button></p>}
    <section className="session-create"><form onSubmit={create}><div><label htmlFor="session-title">New session</label><input id="session-title" required maxLength={120} value={title} onChange={e => setTitle(e.target.value)} placeholder="Give this session a title"/><label htmlFor="session-description">Description <span>(optional)</span></label><textarea id="session-description" maxLength={500} value={description} onChange={e => setDescription(e.target.value)} placeholder="What will you be exploring?" rows={2}/></div><label htmlFor="twitch-channel-id">Twitch channel ID <span>(optional; needed for the Extension)</span></label><input id="twitch-channel-id" inputMode="numeric" pattern="[0-9]*" maxLength={32} value={twitchChannelId} onChange={e => setTwitchChannelId(e.target.value)} placeholder="Numeric channel ID"/><button disabled={busy} type="submit">Create session ↗</button></form></section>
    <section className="session-list" id="sessions"><header><h2>Sessions</h2><span>Saved to your account</span></header>{sessions.length === 0 ? <div className="session-empty"><h3>No sessions yet.</h3><p>Create a session when you’re ready to collect audience curiosity. Starting a session does not connect Twitch in this stage.</p></div> : sessions.map(session => <article className="session-row" key={session.id}><div className="session-info"><span className={`session-status status-${session.status}`}>{session.status}</span><h3><Link href={`/workspace/sessions/${session.id}`}>{session.title}</Link></h3>{session.description && <p>{session.description}</p>}<small>Created {new Date(session.created_at).toLocaleDateString()}</small></div><div className="session-actions"><Link href={`/workspace/sessions/${session.id}`}>Session details ↗</Link>{session.status === "live" && <Link href={`/view/${session.public_token}`}>Viewer preview ↗</Link>}{session.status === "draft" && <button disabled={busy} onClick={() => void transition(session,"start")}>Start</button>}{session.status === "live" && <button disabled={busy} onClick={() => void transition(session,"end")}>End session</button>}<span>{session.status === "ended" ? "Session complete" : session.status === "live" ? "Live locally" : "Ready when you are"}</span></div></article>)}</section>
    <footer className="footerline"><Link href="/">← OPSYRO</Link><span>Workspace data is private to your account.</span></footer></main></div>;
}



