import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { api, authSession, login as loginRequest } from "../api/client";

type AuthValue = { status: "checking" | "authenticated" | "anonymous"; login: (u: string, p: string) => Promise<boolean>; logout: () => void };
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthValue["status"]>(authSession.get() ? "checking" : "anonymous");
  useEffect(() => { if (status === "checking") void api.me().then((r) => setStatus(r.state === "success" ? "authenticated" : "anonymous")); }, [status]);
  const value = useMemo<AuthValue>(() => ({
    status,
    login: async (u, p) => { const r = await loginRequest(u, p); const ok = r.state === "success"; setStatus(ok ? "authenticated" : "anonymous"); return ok; },
    logout: () => { authSession.clear(); setStatus("anonymous"); },
  }), [status]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("AuthProvider missing"); return value; }
export function RequireAuth({ children }: { children: ReactNode }) {
  const auth = useAuth(); const location = useLocation();
  if (auth.status === "checking") return <div className="center-state" role="status">Securing your engineering workspace…</div>;
  if (auth.status === "anonymous") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}
