"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import Brand from "@/components/Brand";

export default function AuthForm({ mode }: { mode: "sign-in" | "register" }) {
  const registering = mode === "register";
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setSuccess("");
    try {
      if (registering) {
        await api.register({ username, email, password });
        setSuccess("Account created. Sign in to open your workspace.");
      } else {
        await api.login({ username, password });
        window.location.assign("/workspace");
      }
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not complete this request."); }
    finally { setBusy(false); }
  }
  return <main className="auth-page"><Brand/><section className="auth-panel"><p className="eyebrow">CREATOR WORKSPACE</p><h1>{registering ? "Create your account" : "Welcome back"}</h1><p className="auth-intro">{registering ? "Set up an OPSYRO creator account to manage your sessions." : "Sign in to continue to your creator workspace."}</p><form onSubmit={submit}>
    <label htmlFor="username">Username</label><input id="username" autoComplete="username" required minLength={3} maxLength={150} value={username} onChange={e => setUsername(e.target.value)}/>
    {registering && <><label htmlFor="email">Email</label><input id="email" type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)}/></>}
    <label htmlFor="password">Password</label><input id="password" type="password" autoComplete={registering ? "new-password" : "current-password"} required minLength={registering ? 10 : undefined} value={password} onChange={e => setPassword(e.target.value)}/>
    {error && <p className="auth-message error" role="alert">{error}</p>}{success && <p className="auth-message success" role="status">{success}</p>}
    <button disabled={busy} type="submit">{busy ? "Working…" : registering ? "Create account" : "Sign in"}<span>↗</span></button></form><p className="auth-switch">{registering ? <>Already have an account? <Link href="/sign-in">Sign in</Link></> : <>New to OPSYRO? <Link href="/register">Create an account</Link></>}</p><p className="auth-footnote">Connect Twitch from your creator workspace after signing in.</p></section></main>;
}
