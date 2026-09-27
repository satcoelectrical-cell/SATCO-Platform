import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import {
  api,
  authSession,
  login as loginRequest,
  logout as logoutRequest,
  startMfaEnrollment,
  verifyMfaEnrollment,
  verifyMfaLogin,
  type MfaEnrollment,
} from "../api/client";
import type { UserProfile } from "../api/types";

type AuthStatus = "checking" | "anonymous" | "primary_auth_pending" | "mfa_required" | "recovery_required" | "authenticated";
type LoginResult = "authenticated" | "mfa_required" | "failed";
type MfaResult = "authenticated" | "recovery_required" | "failed";
type MfaState = {
  challenge: string;
  enrollmentRequired: boolean;
  enrollment: MfaEnrollment | null;
  recoveryCodes: string[];
};
type AuthValue = {
  status: AuthStatus;
  profile: UserProfile | null;
  mfa: MfaState | null;
  login: (u: string, p: string) => Promise<LoginResult>;
  completeMfa: (code: string) => Promise<MfaResult>;
  acknowledgeRecoveryCodes: () => Promise<void>;
  cancelMfa: () => void;
  logout: () => void;
  refreshProfile: () => Promise<void>;
};
const AuthContext = createContext<AuthValue | null>(null);

const AUTH_CHANNEL_NAME = "satco.auth.v1";
type AuthChannelMessage = { type: "logout" };

function createAuthChannel(): BroadcastChannel | null {
  if (typeof BroadcastChannel === "undefined") return null;
  return new BroadcastChannel(AUTH_CHANNEL_NAME);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("checking");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [mfa, setMfa] = useState<MfaState | null>(null);
  async function refreshProfile() { const result = await api.me(); if (result.state === "success") { setProfile(result.data); setStatus("authenticated"); } else { setProfile(null); setStatus("anonymous"); } }
  useEffect(() => { if (status === "checking") void refreshProfile(); }, [status]);

  useEffect(() => {
    const channel = createAuthChannel();
    if (!channel) return;

    channel.onmessage = (event: MessageEvent<AuthChannelMessage>) => {
      if (event.data?.type !== "logout") return;
      authSession.clear();
      setProfile(null);
      setMfa(null);
      setStatus("anonymous");
    };

    return () => channel.close();
  }, []);
  const value = useMemo<AuthValue>(() => ({
    status,
    profile,
    mfa,
    login: async (u, p) => {
      setStatus("primary_auth_pending");
      setMfa(null);
      const result = await loginRequest(u, p);
      if (result.state !== "success") {
        setStatus("anonymous");
        return "failed";
      }
      if (result.data.outcome === "authenticated") {
        await refreshProfile();
        return "authenticated";
      }

      let next: MfaState = {
        challenge: result.data.challenge,
        enrollmentRequired: result.data.enrollmentRequired,
        enrollment: null,
        recoveryCodes: [],
      };
      if (result.data.enrollmentRequired) {
        const enrollment = await startMfaEnrollment(result.data.challenge);
        if (enrollment.state !== "success") {
          setStatus("anonymous");
          return "failed";
        }
        next = {
          ...next,
          challenge: enrollment.data.challenge,
          enrollment: enrollment.data,
        };
      }
      setMfa(next);
      setStatus("mfa_required");
      return "mfa_required";
    },
    completeMfa: async (code) => {
      if (!mfa) return "failed";
      const result = mfa.enrollmentRequired
        ? await verifyMfaEnrollment(mfa.challenge, code)
        : await verifyMfaLogin(mfa.challenge, code);
      if (result.state !== "success") return "failed";
      if (mfa.enrollmentRequired) {
        setMfa({ ...mfa, recoveryCodes: result.data as string[] });
        setStatus("recovery_required");
        return "recovery_required";
      }
      setMfa(null);
      await refreshProfile();
      return "authenticated";
    },
    acknowledgeRecoveryCodes: async () => {
      if (status !== "recovery_required" || !mfa?.recoveryCodes.length) return;
      setMfa(null);
      await refreshProfile();
    },
    cancelMfa: () => {
      const hadAuthority = Boolean(authSession.get());
      authSession.clear();
      setMfa(null);
      setProfile(null);
      setStatus("anonymous");
      if (hadAuthority) void logoutRequest();
    },
    logout: () => {
      setProfile(null);
      setMfa(null);
      setStatus("anonymous");

      const channel = createAuthChannel();
      channel?.postMessage({ type: "logout" } satisfies AuthChannelMessage);
      channel?.close();

      void logoutRequest();
    },
    refreshProfile,
  }), [status, profile, mfa]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error("AuthProvider missing"); return value; }
export function RequireAuth({ children }: { children: ReactNode }) {
  const auth = useAuth(); const location = useLocation();
  if (auth.status === "checking") return <div className="center-state" role="status">Securing your engineering workspace…</div>;
  if (auth.status === "authenticated") return children;
  return <Navigate to="/login" replace state={{ from: location.pathname }} />;
}
