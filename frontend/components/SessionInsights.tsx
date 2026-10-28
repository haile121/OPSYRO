"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, AttentionMap, CreatorSession, QuestionCluster, SessionSummary } from "@/lib/api";
import { useSessionStream } from "@/lib/useSessionStream";
import ResponseEditor from "@/components/ResponseEditor";

export default function SessionInsights({ id }: { id: string }) {
  const [session, setSession] = useState<CreatorSession | null>(null);
  const [attention, setAttention] = useState<AttentionMap | null>(null);
  const [questions, setQuestions] = useState<QuestionCluster[]>([]);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setBusy(true); setError("");
    try { const [item, map, clusters, totals] = await Promise.all([api.session(id), api.attention(id), api.questions(id), api.summary(id)]); setSession(item); setAttention(map); setQuestions(clusters); setSummary(totals); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load this session."); }
    finally { setBusy(false); }
  }, [id]);
  useEffect(() => { void load(); }, [load]);
  const stream = useSessionStream(id, () => { void load(); });
  const cells = new Map(attention?.cells.map(cell => [`${cell.x}:${cell.y}`, cell.count]) || []);
  return <main className="insights-page"><header className="demo-nav"><Link className="wordmark" href="/">◢ OPSYRO</Link><Link href="/workspace">← Workspace</Link></header>{busy ? <p className="insights-loading">Loading session details…</p> : error ? <section className="insights-error"><h1>Could not open this session.</h1><p>{error}</p><button onClick={() => void load()}>Retry</button></section> : session && <>
    <header className="insights-title"><div><p className="eyebrow">SESSION / {session.status.toUpperCase()}</p><h1>{session.title}</h1><p>{session.description || "No session description."}</p></div><div className="insights-actions"><span className={`stream-state stream-${stream}`}>{stream === "connected" ? "Live updates on" : stream === "offline" ? "Live updates unavailable" : "Connecting live updates"}</span>{session.status === "live" && <Link className="primary-action" href={`/view/${session.public_token}`}>Open viewer preview ↗</Link>}<button onClick={() => void load()}>Refresh</button></div></header>
    <div className="insights-stats"><div><strong>{summary?.signal_count || 0}</strong><span>audience signals</span></div><div><strong>{summary?.question_groups || 0}</strong><span>question groups</span></div><div><strong>{summary?.helpful_feedback_count || 0}/{summary?.feedback_count || 0}</strong><span>viewers helped</span></div></div>
    <div className="insights-layout"><section className="attention-panel"><header><div><p className="eyebrow">WHERE ATTENTION LANDED</p><h2>Attention map</h2></div><span>10 × 10 view</span></header>{attention?.signal_count ? <><div className="attention-grid" role="img" aria-label={`Attention map with ${attention.signal_count} audience signals. ${attention.region_summary.map(r=>`${r.region_key}: ${r.count}`).join("; ")}`}>
      {Array.from({length:100},(_,index)=>{const x=index%10,y=Math.floor(index/10),count=cells.get(`${x}:${y}`)||0;return <span key={index} title={`${count} signals`} style={{backgroundColor:count?`rgba(81,70,216,${Math.min(.15+Math.log1p(count)/3,.9)})`:"#f0efeb"}}>{count||""}</span>})}</div><p className="map-alt">Signal totals by selected detail</p><ul className="region-list">{attention.region_summary.length ? attention.region_summary.map(region=><li key={region.region_key}><span>{region.region_key}</span><b>{region.count}</b></li>) : <li><span>Signals without a named detail</span><b>{attention.signal_count}</b></li>}</ul></> : <div className="insights-empty"><h3>No audience signals yet.</h3><p>Start this session and share its viewer preview link to collect sample feedback.</p></div>}</section>
    <section className="questions-panel"><header><div><p className="eyebrow">RECURRING CURIOSITY</p><h2>Question groups</h2></div><span>{questions.length} groups</span></header>{questions.length ? questions.map(group=><article className="question-cluster" key={group.id}><div><h3>{group.label}</h3><span>{group.signal_count} {group.signal_count===1?"signal":"signals"}{group.region_key?` · ${group.region_key}`:""}</span></div>{group.example_questions.map((question,index)=><p key={`${group.id}-${index}`}>“{question}”</p>)}<ResponseEditor clusterId={group.id} response={group.creator_response} onChanged={() => void load()}/></article>) : <div className="insights-empty"><h3>No recurring questions yet.</h3><p>As viewers send questions, related ones will appear together here.</p></div>}</section></div>
    <p className="integration-boundary">Viewer preview uses the session’s local share link. Twitch Extension authorization is not configured.</p>
  </>}</main>;
}
