import { act, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, RequireAuth, useAuth } from "../auth/AuthProvider";
import {
  api,
  login,
  logout,
  startMfaEnrollment,
  verifyMfaEnrollment,
  verifyMfaLogin,
} from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    me: vi.fn(),
  },
  login: vi.fn(),
  logout: vi.fn(),
  authSession: { get: vi.fn(() => null), clear: vi.fn() },
  startMfaEnrollment: vi.fn(),
  verifyMfaEnrollment: vi.fn(),
  verifyMfaLogin: vi.fn(),
}));

function Probe() {
  const auth = useAuth();

  return (
    <div>
      <span data-testid="status">{auth.status}</span>
      <span data-testid="profile">{auth.profile?.username ?? "none"}</span>
      <span data-testid="mfa-state">{auth.mfa ? "present" : "none"}</span>
      <button type="button" onClick={() => void auth.login("admin", "secret")}>login</button>
      <button type="button" onClick={() => void auth.completeMfa("123456")}>verify mfa</button>
      <button type="button" onClick={auth.logout}>logout</button>
    </div>
  );
}

describe("PATCH-058 C3 AuthProvider browser-session restoration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("attempts server-authoritative restoration on cold start", async () => {
    vi.mocked(api.me).mockResolvedValue({
      state: "success",
      data: {
        id: 7,
        username: "engineer",
        email: "engineer@example.com",
        full_name: "Engineer",
        role: "engineer",
        organization: {
          id: "org-1",
          name: "SATCO",
          slug: "satco",
        },
      },
    } as never);

    render(
      <MemoryRouter>
        <AuthProvider>
          <Probe />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.getByTestId("status")).toHaveTextContent("checking");

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    expect(api.me).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("profile")).toHaveTextContent("engineer");
  });

  it("settles anonymous when server-authoritative restoration fails", async () => {
    vi.mocked(api.me).mockResolvedValue({ state: "protected" });

    render(
      <MemoryRouter>
        <AuthProvider>
          <Probe />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });

    expect(api.me).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("profile")).toHaveTextContent("none");
  });

  it("uses server-backed logout and clears provider authority immediately", async () => {
    vi.mocked(api.me).mockResolvedValue({
      state: "success",
      data: {
        id: 7,
        username: "engineer",
        email: "engineer@example.com",
        full_name: "Engineer",
        role: "engineer",
        organization: {
          id: "org-1",
          name: "SATCO",
          slug: "satco",
        },
      },
    } as never);

    vi.mocked(logout).mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <AuthProvider>
          <Probe />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    await act(async () => {
      screen.getByRole("button", { name: "logout" }).click();
    });

    expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    expect(screen.getByTestId("profile")).toHaveTextContent("none");
    expect(logout).toHaveBeenCalledTimes(1);
  });
});

describe("PATCH-058 C3 MFA browser state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    localStorage.clear();
    vi.mocked(api.me).mockResolvedValue({ state: "protected" });
  });

  it("keeps an active-factor challenge only in provider memory", async () => {
    vi.mocked(login).mockResolvedValue({
      state: "success",
      data: {
        outcome: "mfa_required",
        challenge: "challenge-secret",
        enrollmentRequired: false,
      },
    });

    render(<MemoryRouter><AuthProvider><Probe /></AuthProvider></MemoryRouter>);
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));
    await act(async () => { screen.getByRole("button", { name: "login" }).click(); });
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("mfa_required"));

    expect(screen.getByTestId("mfa-state")).toHaveTextContent("present");
    expect(startMfaEnrollment).not.toHaveBeenCalled();
    expect(sessionStorage.length).toBe(0);
    expect(localStorage.length).toBe(0);
  });

  it("holds enrollment and recovery credentials in memory without browser storage", async () => {
    vi.mocked(login).mockResolvedValue({
      state: "success",
      data: {
        outcome: "mfa_required",
        challenge: "initial-challenge",
        enrollmentRequired: true,
      },
    });
    vi.mocked(startMfaEnrollment).mockResolvedValue({
      state: "success",
      data: {
        challenge: "verification-challenge",
        secret: "TOTPSECRET",
        provisioningUri: "otpauth://totp/SATCO",
      },
    });
    vi.mocked(verifyMfaEnrollment).mockResolvedValue({
      state: "success",
      data: ["recovery-one", "recovery-two"],
    });

    render(<MemoryRouter><AuthProvider><Probe /></AuthProvider></MemoryRouter>);
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));
    await act(async () => { screen.getByRole("button", { name: "login" }).click(); });
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("mfa_required"));
    await act(async () => { screen.getByRole("button", { name: "verify mfa" }).click(); });
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("recovery_required"));

    expect(startMfaEnrollment).toHaveBeenCalledWith("initial-challenge");
    expect(verifyMfaEnrollment).toHaveBeenCalledWith("verification-challenge", "123456");
    expect(verifyMfaLogin).not.toHaveBeenCalled();
    expect(sessionStorage.length).toBe(0);
    expect(localStorage.length).toBe(0);
  });

  it("removes protected routes while MFA assurance is pending", async () => {
    vi.mocked(api.me).mockResolvedValue({
      state: "success",
      data: {
        id: 7,
        username: "engineer",
        email: "engineer@example.com",
        full_name: "Engineer",
        role: "engineer",
        organization: { id: "org-1", name: "SATCO", slug: "satco" },
      },
    } as never);
    vi.mocked(login).mockResolvedValue({
      state: "success",
      data: {
        outcome: "mfa_required",
        challenge: "challenge-secret",
        enrollmentRequired: false,
      },
    });

    render(
      <MemoryRouter initialEntries={["/private"]}>
        <AuthProvider>
          <Probe />
          <Routes>
            <Route path="/login" element={<span>login boundary</span>} />
            <Route path="/private" element={<RequireAuth><span>sensitive workspace</span></RequireAuth>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("sensitive workspace")).toBeVisible());

    await act(async () => { screen.getByRole("button", { name: "login" }).click(); });

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("mfa_required"));
    expect(screen.getByText("login boundary")).toBeVisible();
    expect(screen.queryByText("sensitive workspace")).not.toBeInTheDocument();
  });
});

describe("PATCH-058 C3 cross-tab authentication coordination", () => {
  it("broadcasts only a non-secret logout event", async () => {
    const posted: unknown[] = [];
    const close = vi.fn();

    class MockBroadcastChannel {
      onmessage: ((event: MessageEvent) => void) | null = null;
      constructor(public name: string) {}
      postMessage(value: unknown) { posted.push(value); }
      close() { close(); }
    }

    vi.stubGlobal("BroadcastChannel", MockBroadcastChannel);

    vi.mocked(api.me).mockResolvedValue({
      state: "success",
      data: {
        id: 7,
        username: "engineer",
        email: "engineer@example.com",
        full_name: "Engineer",
        role: "engineer",
        organization: {
          id: "org-1",
          name: "SATCO",
          slug: "satco",
        },
      },
    } as never);
    vi.mocked(logout).mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <AuthProvider>
          <Probe />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    await act(async () => {
      screen.getByRole("button", { name: "logout" }).click();
    });

    expect(posted).toEqual([{ type: "logout" }]);
    expect(JSON.stringify(posted)).not.toMatch(
      /access.?token|refresh|csrf|organization|project|workspace|credential/i,
    );
  });

  it("settles anonymous when another tab broadcasts logout", async () => {
    let receiver: ((event: MessageEvent) => void) | null = null;

    class MockBroadcastChannel {
      onmessage: ((event: MessageEvent) => void) | null = null;

      constructor(public name: string) {
        queueMicrotask(() => {
          receiver = this.onmessage;
        });
      }

      postMessage() {}
      close() {}
    }

    vi.stubGlobal("BroadcastChannel", MockBroadcastChannel);

    vi.mocked(api.me).mockResolvedValue({
      state: "success",
      data: {
        id: 7,
        username: "engineer",
        email: "engineer@example.com",
        full_name: "Engineer",
        role: "engineer",
        organization: {
          id: "org-1",
          name: "SATCO",
          slug: "satco",
        },
      },
    } as never);

    render(
      <MemoryRouter>
        <AuthProvider>
          <Probe />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
      expect(receiver).not.toBeNull();
    });

    await act(async () => {
      receiver?.({ data: { type: "logout" } } as MessageEvent);
    });

    expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    expect(screen.getByTestId("profile")).toHaveTextContent("none");
  });
});
