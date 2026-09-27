import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthProvider";

function CredentialPage({ purpose }: { purpose: "activate" | "reset" }) {
  const [params, setParams] = useSearchParams(); const navigate = useNavigate();
  const [token, setToken] = useState(() => params.get("token") ?? ""); const [password, setPassword] = useState(""); const [state, setState] = useState("");

  useEffect(() => {
    if (!params.has("token")) return;
    const sanitized = new URLSearchParams(params);
    sanitized.delete("token");
    setParams(sanitized, { replace: true });
  }, [params, setParams]);
  async function submit(event: FormEvent) { event.preventDefault(); const result = purpose === "activate" ? await api.activateAccount(token, password) : await api.resetAccount(token, password); if (result.state === "success") navigate("/login", { replace: true }); else setState("The credential was not accepted. Request a new one from an administrator."); }
  return <main className="login-page"><section className="login-brand"><div className="brand-mark large">S</div><span className="eyebrow">Governed account access</span><h1>{purpose === "activate" ? "Activate your SATCO account." : "Reset your SATCO password."}</h1><p>Single-use credentials are verified by the server and never retained in this browser.</p></section><section className="login-panel"><form onSubmit={submit}><h2>{purpose === "activate" ? "Account activation" : "Password reset"}</h2><label>One-time credential<input value={token} onChange={(e) => setToken(e.target.value)} minLength={40} autoComplete="one-time-code" required /></label><label>New password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={12} autoComplete="new-password" required /></label>{state && <div className="form-error" role="alert">{state}</div>}<button className="button primary full">{purpose === "activate" ? "Activate account" : "Set new password"}</button><Link className="text-link" to="/login">Return to sign in</Link></form></section></main>;
}

export function ActivatePage() { return <CredentialPage purpose="activate" />; }
export function ResetPage() { return <CredentialPage purpose="reset" />; }

export function BootstrapPage() {
  const [key, setKey] = useState(""); const [name, setName] = useState(""); const [slug, setSlug] = useState(""); const [username, setUsername] = useState(""); const [email, setEmail] = useState(""); const [token, setToken] = useState<string | null>(null); const [failed, setFailed] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setFailed(false); const result = await api.bootstrapOrganization({ organization_name: name, organization_slug: slug, admin_username: username, admin_email: email }, key); if (result.state === "success" && result.data.one_time_token) setToken(result.data.one_time_token); else setFailed(true); }
  return <main className="login-page"><section className="login-brand"><div className="brand-mark large">S</div><span className="eyebrow">Platform bootstrap</span><h1>Initialize the first governed Organization.</h1><p>This bounded operator workflow is not public registration. The bootstrap credential remains browser-memory only.</p></section><section className="login-panel"><form onSubmit={submit}><h2>Organization and initial admin</h2><label>Platform bootstrap key<input type="password" value={key} onChange={(e) => setKey(e.target.value)} minLength={32} required /></label><label>Organization name<input value={name} onChange={(e) => setName(e.target.value)} minLength={2} required /></label><label>Organization slug<input value={slug} onChange={(e) => setSlug(e.target.value)} pattern="[a-z0-9]+(?:-[a-z0-9]+)*" required /></label><label>Admin username<input value={username} onChange={(e) => setUsername(e.target.value)} required /></label><label>Admin email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>{failed && <div className="form-error" role="alert">Bootstrap was not accepted.</div>}{token ? <div className="one-time-secret" role="status"><strong>Copy this activation credential now</strong><code>{token}</code><span>It will not be shown again.</span></div> : <button className="button primary full">Create governed Organization</button>}<Link className="text-link" to="/login">Return to sign in</Link></form></section></main>;
}

export function SecurityRecoveryPage({ purpose }: { purpose: "account" | "mfa" }) {
  const navigate = useNavigate();
  const [credential, setCredential] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage("");
    const result = purpose === "account"
      ? await api.completeAccountRecovery(credential, password)
      : await api.completeMfaRecovery(credential);
    setBusy(false);
    if (result.state === "success") navigate("/login", { replace: true });
    else setMessage("The recovery credential was not accepted or has expired.");
  }
  return <main className="login-page"><section className="login-brand"><div className="brand-mark large">S</div><span className="eyebrow">Human-controlled recovery</span><h1>{purpose === "account" ? "Recover account access." : "Recover MFA access."}</h1><p>Use only the bounded recovery credential issued by your Organization administrator. It is single-use and is not retained in browser storage.</p></section><section className="login-panel"><form onSubmit={submit}><h2>{purpose === "account" ? "Account recovery" : "MFA recovery"}</h2><label>Recovery credential<input value={credential} onChange={(e) => setCredential(e.target.value)} minLength={55} maxLength={256} autoComplete="off" required /></label>{purpose === "account" && <label>New password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={12} maxLength={512} autoComplete="new-password" required /></label>}{message && <div className="form-error" role="alert">{message}</div>}<button className="button primary full" disabled={busy}>{busy ? "Verifying…" : "Complete recovery"}</button><Link className="text-link" to="/login">Return to sign in</Link></form></section></main>;
}

export function AccountPage() {
  const auth = useAuth();
  const [current, setCurrent] = useState(""); const [next, setNext] = useState("");
  const [message, setMessage] = useState(""); const [stepPassword, setStepPassword] = useState(""); const [totp, setTotp] = useState("");
  const [recent, setRecent] = useState(false); const [codes, setCodes] = useState<string[]>([]);
  const [mfa, setMfa] = useState<{ required:boolean; enrolled:boolean; active:boolean } | null>(null);
  const [sessions, setSessions] = useState<{ id:string; current:boolean; created_at:string; expires_at:string; device_label:string|null }[]>([]);
  async function loadSecurity() {
    const [mfaResult, sessionResult] = await Promise.all([api.mfaStatus(), api.sessions()]);
    if (mfaResult.state === "success") setMfa(mfaResult.data);
    if (sessionResult.state === "success") setSessions(sessionResult.data.sessions);
  }
  useEffect(() => { void loadSecurity(); }, []);
  async function submit(event: FormEvent) { event.preventDefault(); const result = await api.changePassword(current, next); if (result.state === "success") { auth.logout(); setMessage("Password changed. Sign in again with the new password."); } else setMessage("Password change was not accepted."); }
  async function establishRecent(event: FormEvent) { event.preventDefault(); const result = await api.stepUp(stepPassword, totp || undefined); setStepPassword(""); setTotp(""); if (result.state === "success") { setRecent(true); setMessage("Recent authentication established for sensitive account actions."); } else setMessage("Recent authentication was not accepted."); }
  async function regenerate() { if (!recent) return; const result = await api.regenerateRecoveryCodes(); if (result.state === "success") { setCodes(result.data.recovery_codes); setMessage("New recovery codes issued. Save them now; older unused codes are no longer valid."); } else setMessage("Recovery-code regeneration was not accepted."); }
  async function endAll() { if (!recent || !window.confirm("End all active sessions for this account?")) return; const result = await api.logoutAll(); if (result.state === "success") auth.logout(); else setMessage("Session revocation was not accepted."); }
  return <div className="page"><header className="page-header"><div><span className="eyebrow">Trusted identity</span><h1>My account</h1><p>{auth.profile?.username} · {auth.profile?.organization.name}</p></div></header><div className="account-security-grid"><section className="surface account-surface"><form className="bootstrap-form" onSubmit={submit}><h2>Change password</h2><label>Current password<input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" required /></label><label>New password<input type="password" value={next} onChange={(e) => setNext(e.target.value)} minLength={12} autoComplete="new-password" required /></label><button className="button primary">Change password and end existing sessions</button></form></section><section className="surface account-surface"><div className="surface-header"><h2>Multi-factor authentication</h2><p>{mfa ? `${mfa.required ? "Required" : "Optional"} · ${mfa.active ? "Active" : mfa.enrolled ? "Enrollment pending" : "Not enrolled"}` : "Checking server-authoritative MFA state…"}</p></div><form className="bootstrap-form" onSubmit={establishRecent}><h3>Confirm recent authentication</h3><label>Password<input type="password" value={stepPassword} onChange={(e) => setStepPassword(e.target.value)} autoComplete="current-password" required /></label>{(mfa?.required || mfa?.active) && <label>Authenticator code<input value={totp} onChange={(e) => setTotp(e.target.value.replace(/\D/g, "").slice(0,6))} inputMode="numeric" autoComplete="one-time-code" pattern="\d{6}" minLength={6} maxLength={6} required /></label>}<button className="button ghost">Confirm identity</button></form><div className="security-actions"><button className="button ghost" type="button" disabled={!recent || !mfa?.active} onClick={() => void regenerate()}>Regenerate recovery codes</button><button className="button ghost" type="button" disabled={!recent} onClick={() => void endAll()}>End all sessions</button></div>{codes.length > 0 && <div className="one-time-secret" role="status"><strong>Save these new recovery codes now</strong><ol className="recovery-code-list">{codes.map((code) => <li key={code}><code>{code}</code></li>)}</ol><span>They are shown only in this in-memory view. Do not store them in browser storage or project notes.</span><button className="button ghost compact" type="button" onClick={() => setCodes([])}>I saved them</button></div>}</section><section className="surface account-surface"><div className="surface-header"><h2>Active sessions</h2><p>Server-authoritative session metadata only. Secrets and refresh credentials are never displayed.</p></div><div className="security-session-list">{sessions.map((session) => <article key={session.id}><div><strong>{session.current ? "Current session" : session.device_label || "Browser session"}</strong><span>Created {new Date(session.created_at).toLocaleString()} · expires {new Date(session.expires_at).toLocaleString()}</span></div>{session.current && <span className="badge badge-active">Current</span>}</article>)}</div></section></div>{message && <p className="form-message account-security-message" role="status">{message}</p>}</div>;
}
