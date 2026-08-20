import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { api, authSession, login as loginRequest } from "../api/client";
import type { UserProfile } from "../api/types";

type AuthValue = { status: "checking" | "authenticated" | "anonymous"; profile: UserProfile | null; login: (u: string, p: string) => Promise<boolean>; logout: () => void; refreshProfile: () => Promise<void> };
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthValue["status"]>(authSession.get() ? "checking" : "anonymous");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  async function refreshProfile() { const result = await api.me(); if (result.state === "success") { setProfile(result.data); setStatus("authenticated"); } else { setProfile(null); setStatus("anonymous"); } }
  useEffect(() => { if (status === "checking") void refreshProfile(); }, [status]);
  const value = useMemo<AuthValue>(() => ({
    status,
    profile,
    login: async (u, p) => { const r = await loginRequest(u, p); const ok = r.state === "success"; if (ok) await refreshProfile(); else setStatus("anonymous"); return ok; },
    logout: () => { authSession.clear(); setProfile(null); setStatus("anonymous"); },
    refreshProfile,
  }), [status, profile]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("AuthProvider missing"); return value; }
export function RequireAuth({ children }: { children: ReactNode }) {
  const auth = useAuth(); const location = useLocation();
  if (auth.status === "checking") return <div className="center-state" role="status">Securing your engineering workspace…</div>;
  if (auth.status === "anonymous") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}
