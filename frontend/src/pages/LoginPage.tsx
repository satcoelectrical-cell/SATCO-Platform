import { useState, type FormEvent } from "react";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

export function LoginPage() {
  const auth = useAuth(); const navigate = useNavigate(); const location = useLocation();
  const [username, setUsername] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState(false); const [busy, setBusy] = useState(false);
  if (auth.status === "authenticated") return <Navigate to="/" replace />;
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(false); const ok = await auth.login(username, password); setBusy(false); if (ok) navigate((location.state as { from?: string } | null)?.from ?? "/", { replace: true }); else setError(true); }
  return <main className="login-page"><section className="login-brand"><div className="brand-mark large">S</div><span className="eyebrow">SATCO V1</span><h1>Engineering intelligence.<br /><em>Human governed.</em></h1><p>Enter the command center for projects, evidence, technical knowledge, and bounded AI assistance.</p><div className="trust-list"><span>Canonical engineering context</span><span>Protected Organization scope</span><span>Human authority preserved</span></div></section><section className="login-panel"><form onSubmit={submit}><div className="lock-badge"><LockKeyhole /></div><span className="eyebrow">Secure access</span><h2>Welcome back</h2><p>Use your SATCO credentials. Your Organization context is resolved securely after authentication.</p><label>Username<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label><label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>{error && <div className="form-error" role="alert">Authentication was not accepted.</div>}<button className="button primary full" disabled={busy}>{busy ? "Securing workspace…" : "Enter Command Center"}<ArrowRight size={18} /></button><Link className="text-link" to="/reset">Use a reset credential</Link></form></section></main>;
}
