"use client";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, Creator, CreatorSession, TwitchConnection } from "@/lib/api";
import Brand from "@/components/Brand";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CreatorWorkspace() {
  const [creator, setCreator] = useState<Creator | null>(null);
  const [sessions, setSessions] = useState<CreatorSession[]>([]);
  const [twitch, setTwitch] = useState<TwitchConnection>({ connected: false, profile: null });
  const [twitchNotice, setTwitchNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [unauthorized, setUnauthorized] = useState(false);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [twitchChannelId, setTwitchChannelId] = useState("");
  const [busy, setBusy] = useState(false);
  const [creating, setCreating] = useState(false);
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const user = await api.me(); setCreator(user); setUnauthorized(false);
      const [nextSessions, connection] = await Promise.all([api.sessions(), api.twitchConnection()]);
      setSessions(nextSessions); setTwitch(connection);
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "Unable to load workspace.";
      if (message.includes("Authentication credentials")) setUnauthorized(true);
      else setError(message);
    } finally { setLoading(false); }
  }, []);
  useEffect(() => {
    const result = new URLSearchParams(window.location.search).get("twitch");
    if (result === "connected") setTwitchNotice("Twitch account connected.");
    if (result === "denied") setTwitchNotice("Twitch authorization was cancelled.");
    if (result) window.history.replaceState({}, "", window.location.pathname);
    void load();
  }, [load]);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setCreating(true); setError("");
    try { await api.createSession({ title, description, twitch_channel_id: twitchChannelId }); setTitle(""); setDescription(""); setTwitchChannelId(""); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Session could not be saved."); }
    finally { setCreating(false); }
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
  return <div className="workspace"><aside className="sidebar" aria-label="Workspace navigation"><Brand className="brand"/><p className="nav-label">Workspace</p><nav><a className="nav-item" href="#sessions" aria-current="page">◦ Overview</a><a className="nav-item" href="#sessions">▱ Live sessions</a><Link className="nav-item" href="/workspace/experiments">◌ Experiments</Link></nav><p className="sidebar-note">Audience curiosity, made visible.<br/>Connect Twitch to link your profile</p></aside><main className="main"><header className="topline"><div><p className="eyebrow">Creator workspace</p><h1>Overview</h1></div><div className="creator-controls"><span>{creator?.username}</span><button onClick={signOut}>Sign out</button></div></header><section className="workspace-welcome"><div><p className="eyebrow">YOUR SESSIONS</p><h2>Bring curiosity into view.</h2><p>Create a session to prepare a place for audience questions and attention signals.</p></div><span className="session-count">{sessions.length.toString().padStart(2,"0")}<small>sessions</small></span></section>
    <section className="session-create twitch-connect"><div><p className="eyebrow">TWITCH ACCOUNT</p><h2>{twitch.connected ? `Connected as ${twitch.profile?.display_name}` : "Connect your Twitch account"}</h2><p>{twitch.connected ? `@${twitch.profile?.login} is connected to this OPSYRO creator account.` : "Authorize OPSYRO to identify your Twitch account. Your tokens stay on the backend."}</p></div>{twitch.connected && twitch.profile?.profile_image_url && <img src={twitch.profile.profile_image_url} alt="Twitch profile" width={48} height={48} referrerPolicy="no-referrer"/>}<a className="primary-action" href={`${API_URL}/api/v1/auth/twitch/authorize/`}>{twitch.connected ? "Reconnect Twitch" : "Connect Twitch"}</a></section>
    {twitchNotice && <p className="workspace-success" role="status">{twitchNotice}</p>}
    {error && <p className="workspace-error" role="alert">{error} <button onClick={() => void load()}>Retry</button></p>}
    <section className="session-create new-session" aria-labelledby="new-session-heading">
      <header className="new-session-heading"><div><p className="eyebrow">SESSION SETUP</p><h2 id="new-session-heading">New session</h2><p>Set the context for the questions and moments you’ll explore with your audience.</p></div><span className="new-session-index">01 <i /> SESSION</span></header>
      <form className="new-session-form" onSubmit={create} aria-busy={creating}>
        <label className="new-session-field" htmlFor="session-title"><span className="new-session-label">Session title <span className="field-required">Required</span></span><input id="session-title" required maxLength={120} value={title} onChange={e => setTitle(e.target.value)} placeholder="Give this session a title" aria-describedby="session-title-help"/><small id="session-title-help">A clear title helps you find this session later.</small></label>
        <label className="new-session-field" htmlFor="session-description"><span className="new-session-label">Description <span className="field-optional">Optional</span></span><textarea id="session-description" maxLength={500} value={description} onChange={e => setDescription(e.target.value)} placeholder="What will you be exploring with your audience?" rows={4} aria-describedby="session-description-help"/><small id="session-description-help">Add a little context for this session. Up to 500 characters.</small></label>
        <label className="new-session-field new-session-channel" htmlFor="twitch-channel-id"><span className="new-session-label">Twitch channel ID <span className="field-optional">Optional</span></span><input id="twitch-channel-id" inputMode="numeric" pattern="[0-9]*" maxLength={32} value={twitchChannelId} onChange={e => setTwitchChannelId(e.target.value)} placeholder="e.g. 123456789" aria-describedby="twitch-channel-help"/><small id="twitch-channel-help">Needed only when configuring the Twitch Extension. Enter the numeric ID from your Extension configuration.</small></label>
        <div className="new-session-actions"><span>Your session is saved to your creator account.</span><button disabled={creating} type="submit">{creating ? <>Creating session<span className="button-spinner" aria-hidden="true" /></> : <>Create session <span aria-hidden="true">↗</span></>}</button></div>
      </form>
    </section>
    <section className="session-list" id="sessions"><header><h2>Sessions</h2><span>Saved to your account</span></header>{sessions.length === 0 ? <div className="session-empty"><h3>No sessions yet.</h3><p>Create a session when you’re ready to collect audience curiosity. Starting marks this session live in OPSYRO; viewers can use its preview link.</p></div> : sessions.map(session => <article className="session-row" key={session.id}><div className="session-info"><span className={`session-status status-${session.status}`}>{session.status}</span><h3><Link href={`/workspace/sessions/${session.id}`}>{session.title}</Link></h3>{session.description && <p>{session.description}</p>}<small>Created {new Date(session.created_at).toLocaleDateString()}</small></div><div className="session-actions"><Link href={`/workspace/sessions/${session.id}`}>Session details ↗</Link>{session.status === "live" && <Link href={`/view/${session.public_token}`}>Viewer preview ↗</Link>}{session.status === "draft" && <button disabled={busy} onClick={() => void transition(session,"start")}>Start</button>}{session.status === "live" && <button disabled={busy} onClick={() => void transition(session,"end")}>End session</button>}<span>{session.status === "ended" ? "Session complete" : session.status === "live" ? "Live locally" : "Ready when you are"}</span></div></article>)}</section>
    <footer className="footerline"><Link href="/">← OPSYRO</Link><span>Workspace data is private to your account.</span></footer></main></div>;
}
