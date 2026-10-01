import { useEffect, useRef, useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api/client";
import type { OrganizationMember } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { OrganizationPackageConfigurationPanel } from "../components/OrganizationPackageConfigurationPanel";
import { OrganizationStandardsRightsPanel } from "../components/OrganizationStandardsRightsPanel";
import { CommercialEntitlementPanel } from "../components/CommercialEntitlementPanel";
import { CommercialSeatsPanel } from "../components/CommercialSeatsPanel";

export function OrganizationAdminPage() {
  const auth = useAuth();
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [message, setMessage] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"admin" | "engineer">("engineer");
  const [recentAuth, setRecentAuth] = useState(false);
  const [stepPassword, setStepPassword] = useState("");
  const [stepTotp, setStepTotp] = useState("");
  const [recoveryCredential, setRecoveryCredential] = useState<{ value: string; purpose: string; username: string; expiresAt: string } | null>(null);
  const [stepUpNotice, setStepUpNotice] = useState("");
  const stepUpRef = useRef<HTMLElement>(null);

  async function load() { const result = await api.members(); if (result.state === "success") setMembers(result.data.items); else setMessage("Members could not be disclosed."); }
  useEffect(() => { if (auth.profile?.role === "admin") void load(); }, [auth.profile?.role]);
  if (auth.profile && auth.profile.role !== "admin") return <Navigate to="/" replace />;

  async function provision(event: FormEvent) {
    event.preventDefault(); const result = await api.provisionMember({ username, email, role });
    if (result.state === "success") { setToken(result.data.one_time_token ?? null); setUsername(""); setEmail(""); await load(); }
    else setMessage("Member provisioning was not accepted.");
  }
  async function mutate(member: OrganizationMember, payload: { role?: "admin" | "engineer"; membership_enabled?: boolean; account_active?: boolean }) {
    const destructive = payload.membership_enabled === false || payload.account_active === false || (member.role === "admin" && payload.role === "engineer");
    if (destructive && !window.confirm(`Confirm governed access change for ${member.username}.`)) return;
    const result = await api.mutateMember(member.user_id, { expected_version: member.version, ...payload });
    if (result.state === "success") await load(); else setMessage("The member change was not accepted.");
  }
  async function reset(member: OrganizationMember) { const result = await api.issueMemberReset(member.user_id); if (result.state === "success") setToken(result.data.one_time_token ?? null); else setMessage("Reset issuance was not accepted."); }

  async function stepUp(event: FormEvent) { event.preventDefault(); const result = await api.stepUp(stepPassword, stepTotp || undefined); setStepPassword(""); setStepTotp(""); if (result.state === "success") { setRecentAuth(true); setStepUpNotice(""); setMessage("Recent administrator authentication established for sensitive security actions."); } else setMessage("Recent authentication was not accepted."); }
  function requestCommercialStepUp() { setStepUpNotice("A commercial administration request requires renewed recent authentication. Confirm below, then retry the original action."); stepUpRef.current?.focus(); stepUpRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }); }
  async function revokeSessions(member: OrganizationMember) { if (!recentAuth || !window.confirm(`Revoke all active sessions for ${member.username}?`)) return; const result = await api.revokeMemberSessions(member.user_id); if (result.state === "success") setMessage(`Active sessions revoked for ${member.username}.`); else setMessage("Session revocation was not accepted. Confirm recent authentication and Organization scope."); }
  async function issueRecovery(member: OrganizationMember, purpose: "account_recovery" | "mfa_recovery") { if (!recentAuth) return; const result = await api.issueSecurityRecovery(member.user_id, purpose); if (result.state === "success") setRecoveryCredential({ value: result.data.recovery_credential, purpose, username: member.username, expiresAt: result.data.expires_at }); else setMessage("Recovery issuance was not accepted. Confirm recent authentication and Organization scope."); }

  return <div className="page"><header className="page-header"><div><span className="eyebrow">Current Organization</span><h1>Organization administration</h1><p>Provision and govern members in {auth.profile?.organization.name}. Authority remains server-derived.</p></div></header>
    {token && <div className="one-time-secret surface" role="status"><strong>Copy this one-time credential now</strong><code>{token}</code><span>It will not be shown again.</span><button className="button ghost compact" onClick={() => setToken(null)}>I copied it</button></div>}
    {recoveryCredential && <div className="one-time-secret surface" role="status"><strong>Copy this {recoveryCredential.purpose === "mfa_recovery" ? "MFA" : "account"} recovery credential for {recoveryCredential.username}</strong><code>{recoveryCredential.value}</code><span>Single-use · expires {new Date(recoveryCredential.expiresAt).toLocaleString()} · use only on the corresponding SATCO recovery page.</span><button className="button ghost compact" onClick={() => setRecoveryCredential(null)}>I copied it</button></div>}
    <section ref={stepUpRef} tabIndex={-1} className="surface security-admin-stepup"><div className="surface-header"><h2>Sensitive security administration</h2><p>Session revocation, recovery issuance, entitlement activation, and seat mutations require recent Human authentication. The server remains the authority.</p></div>{stepUpNotice ? <p className="form-message" role="alert">{stepUpNotice}</p> : null}<form className="bootstrap-form security-stepup-form" onSubmit={stepUp}><label>Password<input type="password" value={stepPassword} onChange={(e) => setStepPassword(e.target.value)} autoComplete="current-password" required /></label><label>Authenticator code, when required<input value={stepTotp} onChange={(e) => setStepTotp(e.target.value.replace(/\D/g, "").slice(0,6))} inputMode="numeric" autoComplete="one-time-code" pattern="\d{6}" minLength={6} maxLength={6} /></label><button className="button ghost">Confirm recent authentication</button><span className={`badge ${recentAuth ? "badge-active" : "badge-withdrawn"}`}>{recentAuth ? "Recently authenticated" : "Confirmation required"}</span></form></section>
    <div className="commercial-admin-grid"><CommercialEntitlementPanel onStepUpRequired={requestCommercialStepUp} /><CommercialSeatsPanel onStepUpRequired={requestCommercialStepUp} /></div>
    <div className="admin-grid"><section className="surface"><div className="surface-header"><h2>Provision member</h2><p>No public registration or invitation email is required.</p></div><form className="bootstrap-form" onSubmit={provision}><label>Username<input value={username} onChange={(e) => setUsername(e.target.value)} minLength={3} required /></label><label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label><label>Role<select value={role} onChange={(e) => setRole(e.target.value as "admin" | "engineer")}><option value="engineer">Engineer</option><option value="admin">Admin</option></select></label><button className="button primary">Provision member</button></form></section>
      <section className="surface member-surface"><div className="surface-header"><h2>Members</h2><p>Role, membership, and account state are separate guarded controls.</p></div>{message && <p className="form-message" role="alert">{message}</p>}<div className="member-list">{members.map((member) => <article key={member.user_id}><div><strong>{member.full_name || member.username}</strong><span>{member.username} · {member.email}</span></div><span className={`badge ${member.account_active && member.membership_enabled ? "badge-active" : "badge-withdrawn"}`}>{member.activation_pending ? "Activation pending" : member.account_active && member.membership_enabled ? "Active" : "Disabled"}</span><select aria-label={`Role for ${member.username}`} value={member.role} onChange={(e) => void mutate(member, { role: e.target.value as "admin" | "engineer" })}><option value="engineer">Engineer</option><option value="admin">Admin</option></select><button className="button ghost compact" onClick={() => void mutate(member, { membership_enabled: !member.membership_enabled })}>{member.membership_enabled ? "Disable membership" : "Enable membership"}</button><button className="button ghost compact" disabled={member.activation_pending} onClick={() => void mutate(member, { account_active: !member.account_active })}>{member.account_active ? "Disable account" : "Enable account"}</button><button className="button ghost compact" disabled={member.activation_pending} onClick={() => void reset(member)}>Issue reset</button><button className="button ghost compact" disabled={!recentAuth || member.activation_pending} onClick={() => void revokeSessions(member)}>Revoke sessions</button><button className="button ghost compact" disabled={!recentAuth || member.activation_pending} onClick={() => void issueRecovery(member, "account_recovery")}>Issue account recovery</button><button className="button ghost compact" disabled={!recentAuth || member.activation_pending} onClick={() => void issueRecovery(member, "mfa_recovery")}>Issue MFA recovery</button></article>)}</div></section>
    </div><OrganizationPackageConfigurationPanel /><OrganizationStandardsRightsPanel /></div>;
}
