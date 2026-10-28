"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import CreatorReplies from "@/components/CreatorReplies";

type Part = "dial" | "speaker" | "window" | "circuit";
const parts: Record<Part, { label: string; x: string; y: string }> = {
  dial: { label: "Tuning dial", x: "0.6910", y: "0.7350" },
  speaker: { label: "Speaker", x: "0.4000", y: "0.5820" },
  window: { label: "Frequency window", x: "0.4000", y: "0.5820" },
  circuit: { label: "Circuit board", x: "0.6930", y: "0.4620" },
};
export default function ViewerPreview({ token }: { token: string }) {
  const [part, setPart] = useState<Part | "">("");
  const [question, setQuestion] = useState("");
  const [intent, setIntent] = useState("question");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setMessage(""); setError("");
    if (!part) { setError("Choose a detail in the frame first."); setBusy(false); return; }
    let participant = sessionStorage.getItem(`opsyro:${token}:participant`);
    if (!participant) { participant = crypto.randomUUID(); sessionStorage.setItem(`opsyro:${token}:participant`, participant); }
    const keyName = `opsyro:${token}:retry`;
    let idempotency = sessionStorage.getItem(keyName);
    if (!idempotency) { idempotency = crypto.randomUUID(); sessionStorage.setItem(keyName, idempotency); }
    try {
      const point = parts[part];
      const response = await api.submitSignal({ session_token: token, participant_key: participant, idempotency_key: idempotency, region_x: point.x, region_y: point.y, region_key: part, intent, question: question.trim() });
      sessionStorage.removeItem(keyName); setQuestion(""); setMessage(response.duplicate ? "Your earlier signal was already received." : "Your interest has been shared with the creator.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Your signal could not be sent. You can retry."); }
    finally { setBusy(false); }
  }
  return <main className="viewer-page"><header className="demo-nav"><Link className="wordmark" href="/">◢ OPSYRO</Link><span>LOCAL VIEWER PREVIEW · NOT A TWITCH EXTENSION</span><Link href="/workspace">Creator workspace ↗</Link></header><section className="viewer-intro"><p className="eyebrow">AUDIENCE VIEW / SAMPLE SESSION</p><h1>What caught your attention?</h1><p>Mark a detail in the sample frame. Your response is linked to this creator’s session.</p></section><div className="viewer-layout"><section><div className="demo-art"><span className="art-overline">RESTORATION, LIVE</span><strong>Inside the shortwave radio</strong><svg viewBox="0 0 600 340" role="img" aria-label="Sample radio. Choose one highlighted detail." className="radio-svg"><path d="M44 304h512" stroke="#c9c2b4" strokeWidth="2"/><path d="M110 113 171 67h258l59 46v170H110z" fill="#34343d"/><path d="M132 130h218v132H132z" fill="#c8beab"/><path d="M151 151h180v93H151z" fill="#63717a"/><path d="M169 207c30-29 50-29 76 0 25 26 45 25 73-2" fill="none" stroke="#e7c68e" strokeWidth="4"/><path d="M370 151h91v11h-91zm0 27h91v11h-91zm0 27h91v11h-91z" fill="#aaa18f"/><circle cx="415" cy="250" r="18" fill="#d8cebc"/><circle cx="415" cy="250" r="6" fill="#5c5960"/>
      {([ ["speaker",240,198,52,"SPEAKER",249,142],["window",240,198,29,"WINDOW",169,144],["dial",415,250,35,"DIAL",443,248],["circuit",416,157,46,"CIRCUIT",447,124] ] as const).map(([key,x,y,r,label,tx,ty])=><g key={key} className={part===key?"hotspot selected":"hotspot"} role="button" tabIndex={0} aria-label={`Choose ${parts[key].label}`} onClick={()=>setPart(key)} onKeyDown={e=>{if(e.key==="Enter"||e.key===" ")setPart(key)}}><circle cx={x} cy={y} r={r}/><circle className="point" cx={x} cy={y} r="5"/><text x={tx} y={ty}>{label}</text></g> )}</svg><span className="art-help">Select a highlighted detail</span></div></section><section className="viewer-form-wrap"><form className="viewer-form" onSubmit={submit}><label>What do you want to share?</label><div className="intent-options" role="group" aria-label="Signal type">{[["question","Question"],["curious","Curious"],["confused","Confused"]].map(([key,label])=><button type="button" key={key} aria-pressed={intent===key} onClick={()=>setIntent(key)}>{label}</button>)}</div><p>Marked detail: <b>{part?parts[part].label:"none selected"}</b></p><label htmlFor="viewer-question">Add a question <span>(optional)</span></label><textarea id="viewer-question" maxLength={240} value={question} onChange={e=>setQuestion(e.target.value)} placeholder="What would you like to understand?" rows={3}/><button className="send-signal" type="submit" disabled={busy}>{busy?"Sending…":"Share with creator ↗"}</button>{error&&<p className="viewer-error" role="alert">{error}</p>}{message&&<p className="viewer-success" role="status">{message}</p>}</form><p className="viewer-privacy">This local preview sends a random tab-scoped participant key, selected coordinates, and optional question to the OPSYRO backend. It does not send your name or connect to Twitch.</p></section><CreatorReplies token={token}/></div></main>;
}
