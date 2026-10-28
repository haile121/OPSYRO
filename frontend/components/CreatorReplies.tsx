"use client";
import { useCallback, useEffect, useState } from "react";
import { api, PublicResponse } from "@/lib/api";

export default function CreatorReplies({ token }: { token: string }) {
  const [items, setItems] = useState<PublicResponse[]>([]);
  const [done, setDone] = useState<number[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    try { const result = await api.publicResponses(token); setItems(result.responses); }
    catch { setMessage("Replies are unavailable right now. Try refreshing."); }
    finally { setLoading(false); }
  }, [token]);
  useEffect(() => { const ids = JSON.parse(sessionStorage.getItem(`opsyro:${token}:feedback-done`) || "[]") as number[]; setDone(ids); void load(); }, [load, token]);
  async function helpful(reply: PublicResponse) {
    setMessage("");
    let participant = sessionStorage.getItem(`opsyro:${token}:participant`);
    if (!participant) { participant = crypto.randomUUID(); sessionStorage.setItem(`opsyro:${token}:participant`, participant); }
    const keyName = `opsyro:${token}:feedback:${reply.id}`;
    let key = sessionStorage.getItem(keyName);
    if (!key) { key = crypto.randomUUID(); sessionStorage.setItem(keyName, key); }
    try {
      await api.submitFeedback({ session_token: token, cluster_id: reply.cluster_id, participant_key: participant, idempotency_key: key, helpful: true });
      const next = done.includes(reply.id) ? done : [...done, reply.id]; setDone(next); sessionStorage.setItem(`opsyro:${token}:feedback-done`, JSON.stringify(next)); setMessage("Thanks. Your feedback was recorded."); await load();
    } catch (reason) { setMessage(reason instanceof Error ? reason.message : "Feedback could not be recorded."); }
  }
  return <section className="viewer-replies"><header><div><p className="eyebrow">CREATOR FOLLOW-UP</p><h2>Responses</h2></div><button onClick={() => void load()}>Refresh</button></header>{loading && <p className="reply-empty">Checking for creator responses…</p>}{!loading && !items.length && <p className="reply-empty">No published responses yet. Check back after the creator responds.</p>}{items.map(reply=><article key={reply.id}><small>IN RESPONSE TO</small><p className="reply-question">“{reply.question}”</p><p>{reply.text}</p>{done.includes(reply.id) ? <span className="reply-thanks">Helpful feedback sent ✓</span> : <button onClick={() => void helpful(reply)}>That helped me understand</button>}<span className="reply-total">{reply.helpful_count} viewers found this helpful</span></article>)}{message&&<p className="reply-message" aria-live="polite">{message}</p>}</section>;
}
