import { api, authSession, login, logout, startMfaEnrollment, verifyMfaEnrollment, verifyMfaLogin } from "../api/client";

describe("typed API boundary", () => {
  beforeEach(() => { sessionStorage.clear(); localStorage.clear(); authSession.clear(); vi.restoreAllMocks(); });
  it("keeps access tokens in runtime memory without durable browser persistence", async () => { vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ access_token: "trusted" }), { status: 200 }))); expect((await login("engineer", "secret")).state).toBe("success"); expect(authSession.get()).toBe("trusted"); expect(sessionStorage.length).toBe(0); expect(localStorage.length).toBe(0); });
  it("keeps MFA continuation and enrollment secrets out of browser storage", async () => {
    authSession.clear();
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ outcome: "mfa_required", challenge: "challenge-one", enrollment_required: true }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ outcome: "mfa_enrollment_required", challenge: "challenge-two", secret: "TOTPSECRET", provisioning_uri: "otpauth://totp/SATCO" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "mfa-access", recovery_codes: ["recovery-one"] }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const primary = await login("admin", "secret");
    expect(primary).toEqual({ state: "success", data: { outcome: "mfa_required", challenge: "challenge-one", enrollmentRequired: true } });
    expect(authSession.get()).toBeNull();
    const enrollment = await startMfaEnrollment("challenge-one");
    expect(enrollment.state).toBe("success");
    const completed = await verifyMfaEnrollment("challenge-two", "123456");
    expect(completed).toEqual({ state: "success", data: ["recovery-one"] });
    expect(authSession.get()).toBe("mfa-access");
    expect(sessionStorage.length).toBe(0);
    expect(localStorage.length).toBe(0);
    expect(fetchMock.mock.calls.every(([, init]) => init.credentials === "include")).toBe(true);
  });
  it("does not treat an MFA challenge as normal access authority", async () => {
    authSession.clear();
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ outcome: "mfa_required", challenge: "challenge-one", enrollment_required: false }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "verified-access" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    expect((await login("admin", "secret")).state).toBe("success");
    expect(authSession.get()).toBeNull();
    expect(await verifyMfaLogin("challenge-one", "123456")).toEqual({ state: "success", data: true });
    expect(authSession.get()).toBe("verified-access");
  });
  it("sends bearer authentication without actor or Organization fields", async () => { authSession.set("abc"); const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], total: 0, page: 1, size: 20 }), { status: 200 })); vi.stubGlobal("fetch", fetchMock); await api.projects(); const [url, init] = fetchMock.mock.calls[0]; expect(url).toContain("/projects/"); expect(new Headers(init.headers).get("Authorization")).toBe("Bearer abc"); expect(String(url)).not.toMatch(/actor|organization/i); });
  it.each([[403, "protected"], [404, "protected"], [422, "invalid"], [503, "unavailable"], [500, "error"]])("maps status %s safely", async (status, state) => { vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: Number(status) }))); expect((await api.projects()).state).toBe(state); });
  it("clears an expired session without exposing details", async () => { authSession.set("expired"); vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 401 }))); expect((await api.me()).state).toBe("protected"); expect(authSession.get()).toBeNull(); });
  it("uses bounded accepted integration paths", async () => { const mock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], total: 0 }), { status: 200 })); vi.stubGlobal("fetch", mock); await api.workspaces(7); await api.captures(7); await api.reports(12, 7); await api.memory(12, 7); expect(mock.mock.calls.map(([url]) => String(url))).toEqual(expect.arrayContaining([expect.stringContaining("size=20"), expect.stringContaining("page_size=20")])); });
  it("uses trusted-context bootstrap mutation paths without authority fields", async () => { vi.stubGlobal("crypto", { randomUUID: vi.fn().mockReturnValue("00000000-0000-4000-8000-000000000001") }); const mock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: 1 }), { status: 200 })); vi.stubGlobal("fetch", mock); await api.createCustomer({ name: "Plant" }); await api.createProject({ name: "Relay", customer_id: 1 }); await api.createWorkspace(2, { discipline: "electrical" }); await api.createCapture({ project_id: 2, workspace_id: 3, source_kind: "observation", original_content: "Observed." }); const calls = mock.mock.calls.map(([url, init]) => ({ url: String(url), body: String(init.body ?? ""), headers: new Headers(init.headers) })); expect(calls.map((call) => call.url)).toEqual(expect.arrayContaining([expect.stringContaining("/customers/"), expect.stringContaining("/projects/2/workspaces"), expect.stringContaining("/engineering-experience-captures")])); expect(calls.map((call) => call.body).join(" ")).not.toMatch(/organization_id|actor_id|owner_id/); expect(calls[3].headers.get("Idempotency-Key")).toBe("00000000-0000-4000-8000-000000000001"); });
  it("maps payload-free closed Memory outcomes without treating them as empty success", async () => { vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ outcome: "protected_not_found" }), { status: 200 }))); expect((await api.memory(12, 7)).state).toBe("protected"); });
  it("binds exact admission fields while fixing the accepted audience empty", async () => { vi.stubGlobal("crypto", { randomUUID: vi.fn().mockReturnValue("00000000-0000-4000-8000-000000000001") }); const mock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ outcome: "success", memory_id: "00000000-0000-4000-8000-000000000002", version: 1, standing: "active" }), { status: 200 })); vi.stubGlobal("fetch", mock); await api.admitMemory({ report_id: "00000000-0000-4000-8000-000000000003", accepted_aggregate_version: 2, accepted_snapshot_digest: "a".repeat(64), workspace_id: 9, project_id: 7, admission_rationale: "Human rationale", authority_rationale: "Human authority rationale", reuse_restrictions: [] }); const body = JSON.parse(String(mock.mock.calls[0][1].body)); expect(body.audience_actor_ids).toEqual([]); expect(body).not.toHaveProperty("organization_id"); expect(body.accepted_snapshot_digest).toBe("a".repeat(64)); });
  it("marks exact detail as deliberate reuse with provenance", async () => { const mock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ outcome: "protected_not_found" }), { status: 200 })); vi.stubGlobal("fetch", mock); await api.memoryDetail("00000000-0000-4000-8000-000000000003"); expect(String(mock.mock.calls[0][0])).toContain("include_provenance=true&reuse_intent=true"); });
  it("never sends client-derived Organization or actor fields for member administration", async () => { vi.stubGlobal("crypto", { randomUUID: () => "00000000-0000-4000-8000-000000000001" }); const mock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ outcome: "success" }), { status: 200 })); vi.stubGlobal("fetch", mock); await api.provisionMember({ username: "engineer", email: "e@example.com", role: "engineer" }); const body = String(mock.mock.calls[0][1].body); expect(body).not.toMatch(/organization|actor|issuer/i); expect(new Headers(mock.mock.calls[0][1].headers).get("Idempotency-Key")).toBeTruthy(); });
  it("uses bounded read-only Project Context paths and payload-free status mapping",async()=>{const mock=vi.fn().mockResolvedValue(new Response(JSON.stringify({status:"protected_not_found"}),{status:200}));vi.stubGlobal("fetch",mock);expect((await api.projectContext(7,9)).state).toBe("protected");await api.relatedContext(7,"evidence","00000000-0000-4000-8000-000000000001",9,"opaque");const urls=mock.mock.calls.map(([url])=>String(url));expect(urls[0]).toContain("/projects/7/context?workspace_id=9");expect(urls[1]).toContain("/engineering-context/nodes/evidence/");expect(urls[1]).toContain("continuation=opaque");expect(mock.mock.calls.every(([,init])=>!init.body)).toBe(true);});
});

describe("PATCH-058 C3 bounded refresh coordination", () => {
  beforeEach(() => {
    authSession.clear();
    document.cookie = "satco_csrf=csrf-test-value; path=/";
  });

  it("refreshes once after 401 and retries with the replacement access token", async () => {
    authSession.set("expired-access");

    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response("{}", { status: 401 }))
      .mockResolvedValueOnce(new Response(
        JSON.stringify({ access_token: "replacement-access", token_type: "bearer" }),
        { status: 200 },
      ))
      .mockResolvedValueOnce(new Response(
        JSON.stringify({ id: 1, username: "engineer" }),
        { status: 200 },
      ));

    vi.stubGlobal("fetch", fetchMock);

    const result = await api.me();

    expect(result.state).toBe("success");
    expect(fetchMock).toHaveBeenCalledTimes(3);

    const [refreshUrl, refreshInit] = fetchMock.mock.calls[1];
    expect(refreshUrl).toContain("/auth/refresh");
    expect(refreshInit.credentials).toBe("include");
    expect(new Headers(refreshInit.headers).get("X-CSRF-Token"))
      .toBe("csrf-test-value");

    const [, retryInit] = fetchMock.mock.calls[2];
    expect(new Headers(retryInit.headers).get("Authorization"))
      .toBe("Bearer replacement-access");

    expect(authSession.get()).toBe("replacement-access");
  });

  it("does not refresh or replay an unsafe mutation after 401", async () => {
    authSession.set("expired-access");
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 401 }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await api.createCustomer({ name: "Plant" });

    expect(result.state).toBe("protected");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/customers/");
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("/auth/refresh"))).toBe(false);
    expect(authSession.get()).toBeNull();
  });

  it("fails closed when refresh is rejected", async () => {
    authSession.set("expired-access");

    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response("{}", { status: 401 }))
      .mockResolvedValueOnce(new Response("{}", { status: 401 }));

    vi.stubGlobal("fetch", fetchMock);

    const result = await api.me();

    expect(result.state).toBe("protected");
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(authSession.get()).toBeNull();
  });

  it("coordinates concurrent 401 responses through one refresh request", async () => {
    authSession.set("expired-access");

    let resolveRefresh!: (response: Response) => void;
    const refreshResponse = new Promise<Response>((resolve) => {
      resolveRefresh = resolve;
    });

    let protectedCalls = 0;

    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes("/auth/refresh")) {
        return refreshResponse;
      }

      protectedCalls += 1;

      if (protectedCalls <= 2) {
        return new Response("{}", { status: 401 });
      }

      return new Response(
        JSON.stringify({ id: protectedCalls, username: "engineer" }),
        { status: 200 },
      );
    });

    vi.stubGlobal("fetch", fetchMock);

    const first = api.me();
    const second = api.me();

    await Promise.resolve();
    await Promise.resolve();

    expect(
      fetchMock.mock.calls.filter(([url]) =>
        String(url).includes("/auth/refresh")
      ),
    ).toHaveLength(1);

    resolveRefresh(new Response(
      JSON.stringify({ access_token: "replacement-access", token_type: "bearer" }),
      { status: 200 },
    ));

    const results = await Promise.all([first, second]);

    expect(results.every((result) => result.state === "success")).toBe(true);

    expect(
      fetchMock.mock.calls.filter(([url]) =>
        String(url).includes("/auth/refresh")
      ),
    ).toHaveLength(1);

    expect(authSession.get()).toBe("replacement-access");
  });
});


describe("PATCH-058 C3 server-backed logout", () => {
  beforeEach(() => {
    authSession.clear();
    vi.restoreAllMocks();
  });

  it("invokes server logout with bearer and CSRF before clearing local authority", async () => {
    authSession.set("active-access");
    document.cookie = "satco_csrf=csrf-value; path=/";

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ outcome: "success" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await logout();

    expect(fetchMock).toHaveBeenCalledTimes(1);

    const [url, init] = fetchMock.mock.calls[0];

    expect(url).toContain("/auth/logout");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");

    const headers = new Headers(init.headers);

    expect(headers.get("Authorization")).toBe("Bearer active-access");
    expect(headers.get("X-CSRF-Token")).toBe("csrf-value");
    expect(authSession.get()).toBeNull();
  });

  it("clears local authority even when server logout communication fails", async () => {
    authSession.set("active-access");
    document.cookie = "satco_csrf=csrf-value; path=/";

    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("offline")),
    );

    await expect(logout()).resolves.toBeUndefined();
    expect(authSession.get()).toBeNull();
  });
});
