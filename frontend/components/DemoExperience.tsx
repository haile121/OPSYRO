"use client";
import { FormEvent, useMemo, useState } from "react";

type Part = "dial" | "speaker" | "window" | "circuit";
type Signal = { id: number; part: Part; question: string; helped: boolean };
const labels: Record<Part, string> = { dial: "Tuning dial", speaker: "Speaker", window: "Frequency window", circuit: "Circuit board" };
const start: Signal[] = [
  { id: 1, part: "dial", question: "What does the amber dial change?", helped: false },
  { id: 2, part: "dial", question: "Does the dial tune the signal?", helped: false },
  { id: 3, part: "speaker", question: "Is that the original speaker?", helped: false },
  { id: 4, part: "window", question: "Why does the frequency move?", helped: false },
];
export default function DemoExperience() {
  const [part, setPart] = useState<Part | "">("");
  const [question, setQuestion] = useState("");
  const [signals, setSignals] = useState(start);
  const [responded, setResponded] = useState(false);
  const [message, setMessage] = useState("");
  const groups = useMemo(() => (["dial", "speaker", "window", "circuit"] as Part[]).map((key) => ({ key, items: signals.filter((item) => item.part === key) })).filter((group) => group.items.length), [signals]);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!part || !question.trim()) { setMessage("Choose a detail and add a question first."); return; }
    setSignals((items) => [{ id: Date.now(), part, question: question.trim(), helped: false }, ...items]);
    setQuestion(""); setResponded(false); setMessage("Your question joined the preview signals.");
  }
  function markHelped(id: number) {
    setSignals((items) => items.map((item) => item.id === id ? { ...item, helped: true } : item));
    setMessage("Feedback recorded in this browser preview.");
  }
  const choose = (value: Part) => setPart(value);
  return <div className="demo-content">
    <header className="demo-heading"><div><p className="eyebrow">PRODUCT PREVIEW / RADIO RESTORATION</p><h1>Follow a question<br/>back to its moment.</h1></div><p>Explore how questions take shape.<br/>Interactions stay in your browser.</p></header>
    <div className="demo-grid"><section className="demo-media"><div className="demo-subhead"><h2>Preview media frame</h2><span>00:14 / 02:30</span></div><div className="demo-art"><span className="art-overline">RESTORATION, LIVE</span><strong>Inside the shortwave radio</strong>
      <svg viewBox="0 0 600 340" role="img" aria-label="Illustrative radio scene. Choose a highlighted detail." className="radio-svg">
        <path d="M44 304h512" stroke="#c9c2b4" strokeWidth="2"/><path d="M110 113 171 67h258l59 46v170H110z" fill="#34343d"/><path d="M132 130h218v132H132z" fill="#c8beab"/><path d="M151 151h180v93H151z" fill="#63717a"/><path d="M169 207c30-29 50-29 76 0 25 26 45 25 73-2" fill="none" stroke="#e7c68e" strokeWidth="4"/><path d="M370 151h91v11h-91zm0 27h91v11h-91zm0 27h91v11h-91z" fill="#aaa18f"/><circle cx="415" cy="250" r="18" fill="#d8cebc"/><circle cx="415" cy="250" r="6" fill="#5c5960"/>
        <g className={part === "speaker" ? "hotspot selected" : "hotspot"} role="button" tabIndex={0} aria-label="Choose speaker" onClick={() => choose("speaker")} onKeyDown={e => {if(e.key === "Enter" || e.key === " ") choose("speaker")}}><circle cx="240" cy="198" r="52"/><circle className="point" cx="240" cy="198" r="5"/><text x="249" y="142">SPEAKER</text></g>
        <g className={part === "window" ? "hotspot selected" : "hotspot"} role="button" tabIndex={0} aria-label="Choose frequency window" onClick={() => choose("window")} onKeyDown={e => {if(e.key === "Enter" || e.key === " ") choose("window")}}><circle cx="240" cy="198" r="29"/><circle className="point" cx="240" cy="198" r="5"/><text x="169" y="144">WINDOW</text></g>
        <g className={part === "dial" ? "hotspot selected" : "hotspot"} role="button" tabIndex={0} aria-label="Choose tuning dial" onClick={() => choose("dial")} onKeyDown={e => {if(e.key === "Enter" || e.key === " ") choose("dial")}}><circle cx="415" cy="250" r="35"/><circle className="point" cx="415" cy="250" r="5"/><text x="443" y="248">DIAL</text></g>
        <g className={part === "circuit" ? "hotspot selected" : "hotspot"} role="button" tabIndex={0} aria-label="Choose circuit board" onClick={() => choose("circuit")} onKeyDown={e => {if(e.key === "Enter" || e.key === " ") choose("circuit")}}><circle cx="416" cy="157" r="46"/><circle className="point" cx="416" cy="157" r="5"/><text x="447" y="124">CIRCUIT</text></g>
      </svg><span className="art-help">Select a highlighted detail to mark your interest</span></div>
      <form className="demo-form" onSubmit={submit}><label htmlFor="demo-question">What caught your attention?</label><p>Selected moment: <b>{part ? labels[part] : "choose a detail in the frame"}</b></p><div><input id="demo-question" maxLength={180} value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask a question or share what you noticed…"/><button type="submit">Add signal ↗</button></div><small aria-live="polite">{message || "Your response stays in this browser and clears when you refresh."}</small></form>
    </section><aside className="demo-signals"><div className="signals-title"><div><p className="eyebrow">SHARED CURIOSITY</p><h2>Questions taking shape</h2></div><strong>{signals.length}<small>signals</small></strong></div><p className="signals-explainer">Questions gather around the detail they point to.</p><div className="signal-groups">{groups.map(group => <article key={group.key}><div className="group-heading"><b>● {labels[group.key]}</b><span>{group.items.length} {group.items.length === 1 ? "viewer" : "viewers"}</span></div>{group.items.map(item => <p className="group-question" key={item.id}>“{item.question}”{item.helped && <small>Helpful ✓</small>}</p>)}{group.key === "dial" && <div className="creator-action">{responded ? <><p><b>Creator response</b><br/>The dial changes the receiver’s tuning range, helping isolate nearby frequencies.</p><button onClick={() => markHelped(group.items[0].id)}>That helped me understand</button></> : <button onClick={() => setResponded(true)}>Preview a creator response ↗</button>}</div>}</article>)}</div><p className="preview-note">ⓘ Illustrative activity only · No live Twitch data</p></aside></div>
  </div>;
}
