"use client";
import { FormEvent, useState } from "react";
import { CreatorResponse, api } from "@/lib/api";

export default function ResponseEditor({ clusterId, response, onChanged }: { clusterId: number; response: CreatorResponse | null; onChanged: () => void }) {
  const [text, setText] = useState(response?.text || "");
  const [saved, setSaved] = useState(response);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const value = saved ? await api.updateResponse(saved.id, text) : await api.createResponse(clusterId, text);
      setSaved(value); onChanged();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Draft could not be saved."); }
    finally { setBusy(false); }
  }
  async function publish() {
    if (!saved) return;
    setBusy(true); setError("");
    try { setSaved(await api.publishResponse(saved.id)); onChanged(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Response could not be published."); }
    finally { setBusy(false); }
  }
  if (saved?.status === "published") return <div className="published-response"><p><b>Creator response</b><br/>{saved.text}</p><small>{saved.helpful_count} of {saved.feedback_count} viewers found this helpful</small></div>;
  return <form className="response-editor" onSubmit={save}><label htmlFor={`reply-${clusterId}`}>{saved ? "Edit response draft" : "Draft a response"}</label><textarea id={`reply-${clusterId}`} value={text} onChange={event => setText(event.target.value)} maxLength={2000} rows={3} required placeholder="Write a clear answer for your audience…"/><div><button disabled={busy} type="submit">{busy ? "Saving…" : saved ? "Save draft" : "Save draft reply"}</button>{saved && <button disabled={busy} type="button" onClick={() => void publish()}>Publish response ↗</button>}</div>{error && <p role="alert">{error}</p>}</form>;
}
