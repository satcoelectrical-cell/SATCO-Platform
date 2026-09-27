import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AccountPage, SecurityRecoveryPage } from "../pages/OnboardingPages";
import { OrganizationAdminPage } from "../pages/OrganizationAdminPage";

const logout = vi.fn();
vi.mock("../auth/AuthProvider", () => ({
  useAuth: () => ({
    profile: { id: 1, username: "admin", role: "admin", organization: { id: "o", name: "Acme", slug: "acme" } },
    logout,
  }),
}));

function json(data: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } }));
}

describe("PATCH-058 C4 security administration UI", () => {
  beforeEach(() => { vi.clearAllMocks(); localStorage.clear(); sessionStorage.clear(); });

  it("loads bounded MFA/session metadata and gates sensitive self-service actions behind step-up", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/mfa/status")) return json({ required: true, enrolled: true, active: true });
      if (url.endsWith("/auth/sessions")) return json({ sessions: [{ id: "s1", current: true, created_at: "2026-09-26T08:00:00Z", expires_at: "2026-10-01T08:00:00Z", device_label: null }] });
      if (url.endsWith("/auth/step-up") && init?.method === "POST") return json({ outcome: "success" });
      if (url.endsWith("/auth/mfa/recovery-codes/regenerate") && init?.method === "POST") return json({ outcome: "success", recovery_codes: ["RECOVERY-CODE-0001"] });
      return json({ outcome: "success" });
    }));    render(<MemoryRouter><AccountPage /></MemoryRouter>);
    expect(await screen.findByText(/Required · Active/i)).toBeVisible();
    expect(await screen.findByText("Current session")).toBeVisible();
    const regenerate = screen.getByRole("button", { name: /regenerate recovery codes/i });
    expect(regenerate).toBeDisabled();
    fireEvent.change(screen.getAllByLabelText(/^Password$/i)[0], { target: { value: "correct-password" } });
    fireEvent.change(screen.getByLabelText(/Authenticator code/i), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: /confirm identity/i }));
    await waitFor(() => expect(regenerate).toBeEnabled());
    fireEvent.click(regenerate);
    expect(await screen.findByText("RECOVERY-CODE-0001")).toBeVisible();
    expect(localStorage.length).toBe(0); expect(sessionStorage.length).toBe(0);
  });

  it("completes public account recovery without retaining the credential in browser storage", async () => {
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith("/auth/recovery/account/complete") && init?.method === "POST") return json({ outcome: "success" });
      return json({}, 404);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<MemoryRouter initialEntries={["/recover-account"]}><Routes><Route path="/recover-account" element={<SecurityRecoveryPage purpose="account" />} /><Route path="/login" element={<span>login destination</span>} /></Routes></MemoryRouter>);
    fireEvent.change(screen.getByLabelText(/Recovery credential/i), { target: { value: "r".repeat(60) } });
    fireEvent.change(screen.getByLabelText(/New password/i), { target: { value: "long-enough-password" } });
    fireEvent.click(screen.getByRole("button", { name: /complete recovery/i }));
    expect(await screen.findByText("login destination")).toBeVisible();
    expect(JSON.stringify(fetchMock.mock.calls)).toContain("recovery_credential");
    expect(localStorage.length).toBe(0); expect(sessionStorage.length).toBe(0);
  });
  it("keeps administrator recovery issuance disabled until recent authentication succeeds", async () => {
    const member = { user_id: 7, username: "engineer", email: "e@example.com", full_name: "Engineer", role: "engineer", account_active: true, activation_pending: false, membership_enabled: true, membership_selected: true, version: 1 };
    vi.stubGlobal("crypto", { randomUUID: () => "00000000-0000-4000-8000-000000000001" });
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/step-up") && init?.method === "POST") return json({ outcome: "success" });
      if (url.endsWith("/auth/admin/users/7/recovery") && init?.method === "POST") return json({ outcome: "success", recovery_credential: "x".repeat(60), expires_at: "2026-09-26T12:00:00Z" });
      if (url.endsWith("/organizations/current/standard-rights")) return json({ items: [], next_cursor: null });
      if (url.endsWith("/organizations/current/discipline-package-configuration")) return json({ organization_id: "o", configuration_version: 0, enabled_selections: [], disabled_selections: [], registry_digest: "d".repeat(64), updated_at: null });
      if (url.includes("/discipline-packages/supported")) return json({ registry_digest: "d".repeat(64), items: [], next_cursor: null });
      return json({ outcome: "success", items: [member] });
    }));
    render(<MemoryRouter><OrganizationAdminPage /></MemoryRouter>);
    await screen.findByText("Engineer");
    const issue = screen.getByRole("button", { name: /issue account recovery/i });
    expect(issue).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/^Password$/i), { target: { value: "correct-password" } });
    fireEvent.click(screen.getByRole("button", { name: /confirm recent authentication/i }));
    await waitFor(() => expect(issue).toBeEnabled());
    fireEvent.click(issue);
    expect(await screen.findByText("x".repeat(60))).toBeVisible();
  });
});