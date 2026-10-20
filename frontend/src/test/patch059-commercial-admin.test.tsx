import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { authSession } from "../api/client";
import { CommercialEntitlementPanel } from "../components/CommercialEntitlementPanel";
import { CommercialSeatsPanel } from "../components/CommercialSeatsPanel";
import { OrganizationPackageConfigurationPanel } from "../components/OrganizationPackageConfigurationPanel";

function json(data: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } }));
}

const activeStatus = {
  available: true,
  effective_state: "active",
  entitlement_id: "00000000-0000-4000-8000-000000000059",
  revision: 4,
  digest_prefix: "abcdef012345",
  package_keys: ["control_automation", "electrical", "instrumentation"],
  seat_capacity: 2,
  valid_until: "2026-12-01T00:00:00Z",
  grace_until: "2026-12-15T00:00:00Z",
  support_until: "2026-11-01T00:00:00Z",
  baseline_release_sequence: 1,
  max_release_sequence: 10,
  reason_code: null,
};

describe("PATCH-059 Batch D commercial entitlement administration", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    authSession.clear();
    document.cookie = "satco_csrf=csrf-commercial; path=/";
  });

  it.each([
    ["active", "ACTIVE"],
    ["grace", "GRACE"],
    ["expired", "EXPIRED"],
    ["time_untrusted", "TIME UNTRUSTED"],
  ])("renders the %s status only from the server response", async (effectiveState, label) => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => json({ ...activeStatus, available: effectiveState === "active" || effectiveState === "grace", effective_state: effectiveState, reason_code: effectiveState === "active" ? null : effectiveState })));
    render(<CommercialEntitlementPanel />);
    expect(await screen.findByText(label)).toBeVisible();
    expect(screen.getByText("control automation, electrical, instrumentation")).toBeVisible();
    expect(screen.getByText("abcdef012345")).toBeVisible();
    expect(screen.queryByText(/update eligibility/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/release sequence/i)).not.toBeInTheDocument();
  });

  it("shows the bounded missing-entitlement state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => json({ ...activeStatus, available: false, effective_state: "invalid_or_unavailable", entitlement_id: null, revision: null, digest_prefix: null, package_keys: [], seat_capacity: null, valid_until: null, grace_until: null, support_until: null, reason_code: "entitlement_missing" })));
    render(<CommercialEntitlementPanel />);
    expect(await screen.findByText("No commercial entitlement")).toBeVisible();
    expect(screen.getByText("No commercial entitlement is active for this deployment.")).toBeVisible();
  });

  it("sends the signed envelope unchanged for server validation and explicit activation with CSRF", async () => {
    authSession.set("admin-access");
    const signedEnvelope = "{\n  \"schema\": \"satco.commercial-entitlement/v1\",\n  \"signature\": \"opaque\"\n}";
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/commercial-entitlement/validate")) return json({ valid: true, effect: "successor", entitlement_id: activeStatus.entitlement_id, revision: 4, digest_prefix: "abcdef012345", reason_code: null });
      if (url.endsWith("/commercial-entitlement/activate")) return json({ valid: true, effect: "successor", entitlement_id: activeStatus.entitlement_id, revision: 4, digest_prefix: "abcdef012345", reason_code: null });
      return json(activeStatus);
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<CommercialEntitlementPanel />);
    await screen.findByText("ACTIVE");
    fireEvent.change(screen.getByLabelText("Signed entitlement envelope"), { target: { value: signedEnvelope } });
    fireEvent.click(screen.getByRole("button", { name: "Validate on server" }));
    expect(await screen.findByText("Server validation preview")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Activate validated entitlement" }));
    expect(await screen.findByText("The entitlement was activated by the server.")).toBeVisible();

    const validationCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/commercial-entitlement/validate"));
    const activationCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/commercial-entitlement/activate"));
    expect(validationCall?.[1].body).toBe(signedEnvelope);
    expect(activationCall?.[1].body).toBe(signedEnvelope);
    expect(validationCall?.[1].credentials).toBe("include");
    expect(new Headers(validationCall?.[1].headers).get("X-CSRF-Token")).toBe("csrf-commercial");
    expect(new Headers(validationCall?.[1].headers).get("Authorization")).toBe("Bearer admin-access");
  });

  it("uses a bounded server reason and invokes the existing step-up flow only when the server requires it", async () => {
    let validationAttempt = 0;
    const onStepUpRequired = vi.fn();
    vi.stubGlobal("fetch", vi.fn().mockImplementation((input: RequestInfo | URL) => {
      if (String(input).endsWith("/commercial-entitlement/validate")) {
        validationAttempt += 1;
        return validationAttempt === 1
          ? json({ detail: "Recent authentication required" }, 403)
          : json({ valid: false, effect: "rejected", entitlement_id: null, revision: null, digest_prefix: null, reason_code: "invalid_signature" });
      }
      return json(activeStatus);
    }));
    render(<CommercialEntitlementPanel onStepUpRequired={onStepUpRequired} />);
    await screen.findByText("ACTIVE");
    fireEvent.change(screen.getByLabelText("Signed entitlement envelope"), { target: { value: "opaque signed envelope" } });
    fireEvent.click(screen.getByRole("button", { name: "Validate on server" }));
    await waitFor(() => expect(onStepUpRequired).toHaveBeenCalledOnce());
    expect(screen.getByText(/Confirm it in Sensitive security administration/i)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Validate on server" }));
    expect(await screen.findByText("The signed entitlement was not accepted.")).toBeVisible();
    expect(screen.queryByText("invalid_signature")).not.toBeInTheDocument();
  });

  it("renders all seat states and server-returned executable status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => json({ capacity: 3, consuming_count: 3, over_capacity: false, seats: [
      { user_id: 1, state: "ASSIGNED", executable: true, display_name: "Alpha" },
      { user_id: 2, state: "RESERVED", executable: false, display_name: "Beta" },
      { user_id: 3, state: "RETAINED", executable: true, display_name: "Gamma" },
    ] })));
    render(<CommercialSeatsPanel />);
    expect(await screen.findByText("ASSIGNED")).toBeVisible();
    expect(screen.getByText("RESERVED")).toBeVisible();
    expect(screen.getByText("RETAINED")).toBeVisible();
    expect(screen.getAllByText("EXECUTABLE")).toHaveLength(2);
    expect(screen.getByText("NOT EXECUTABLE")).toBeVisible();
  });

  it("supports assign, release, and an explicit exact retained set without choosing a winner", async () => {
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/commercial-seats/retained") && init?.method === "PUT") return json({ capacity: 1, consuming_count: 2, over_capacity: true, unresolved: true });
      if (/\/commercial-seats\/\d+$/.test(url)) return json({ user_id: Number(url.split("/").at(-1)), state: init?.method === "DELETE" ? null : "RESERVED", consuming_count: 2, capacity: 1 });
      return json({ capacity: 1, consuming_count: 2, over_capacity: true, seats: [
        { user_id: 11, state: "ASSIGNED", executable: false, display_name: "Eleven" },
        { user_id: 12, state: "ASSIGNED", executable: false, display_name: "Twelve" },
      ] });
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<CommercialSeatsPanel />);
    await screen.findByText("OVER CAPACITY");
    const retainedChoices = screen.getAllByRole("checkbox");
    expect(retainedChoices).toHaveLength(2);
    expect(retainedChoices.every((choice) => !(choice as HTMLInputElement).checked)).toBe(true);
    fireEvent.click(retainedChoices[1]);
    fireEvent.click(screen.getByRole("button", { name: "Submit exact retained set" }));
    await screen.findByText(/over-capacity remains unresolved/i);
    const retainedCall = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/commercial-seats/retained") && init?.method === "PUT");
    expect(JSON.parse(String(retainedCall?.[1].body))).toEqual({ user_ids: [12] });

    fireEvent.change(screen.getByLabelText("Current-Organization member ID"), { target: { value: "13" } });
    fireEvent.click(screen.getByRole("button", { name: "Assign seat" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/commercial-seats/13") && init?.method === "POST")).toBe(true));
    fireEvent.click(screen.getAllByRole("button", { name: "Release" })[0]);
    await waitFor(() => expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/commercial-seats/11") && init?.method === "DELETE")).toBe(true));
  });

  it("shows loading and bounded unavailable states without protected detail", async () => {
    let resolveFetch!: (value: Response) => void;
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => new Promise<Response>((resolve) => { resolveFetch = resolve; })));
    render(<CommercialSeatsPanel />);
    expect(screen.getByText("Loading server-derived commercial seats…")).toBeVisible();
    resolveFetch(new Response(JSON.stringify({ detail: "database topology secret" }), { status: 503, headers: { "Content-Type": "application/json" } }));
    expect(await screen.findByText("Service temporarily unavailable")).toBeVisible();
    expect(screen.queryByText("database topology secret")).not.toBeInTheDocument();
  });

  it("uses server-returned package entitlement for usability and reports backend denial", async () => {
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/discipline-package-configuration") && init?.method === "PUT") return json({ detail: "package_not_entitled" }, 409);
      if (url.endsWith("/discipline-package-configuration")) return json({ organization_id: "o", configuration_version: 1, enabled_selections: [], disabled_selections: [], registry_digest: "d".repeat(64), updated_at: null });
      if (url.includes("/discipline-packages/supported")) return json({ registry_digest: "d".repeat(64), items: [
        { package_key: "electrical", package_version: "1", primary_discipline_id: "electrical", standing: "active", descriptor_digest: "a".repeat(64) },
        { package_key: "instrumentation", package_version: "1", primary_discipline_id: "instrumentation", standing: "active", descriptor_digest: "b".repeat(64) },
      ], next_cursor: null });
      return json({ ...activeStatus, package_keys: ["electrical"] });
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<OrganizationPackageConfigurationPanel />);
    const electrical = await screen.findByRole("checkbox", { name: /electrical/i });
    const instrumentation = screen.getByRole("checkbox", { name: /instrumentation/i });
    expect(electrical).toBeEnabled();
    expect(instrumentation).toBeDisabled();
    fireEvent.click(electrical);
    fireEvent.change(screen.getByLabelText("Rationale"), { target: { value: "Authorized admin selection" } });
    fireEvent.click(screen.getByRole("button", { name: "Save package configuration" }));
    expect(await screen.findByText(/server denied this package configuration/i)).toBeVisible();
    expect(screen.queryByText("package_not_entitled")).not.toBeInTheDocument();
  });
});
