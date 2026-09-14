import { beforeEach, expect, it, vi } from "vitest";
import { api } from "../api/client";

beforeEach(() => {
  sessionStorage.clear();
  vi.stubGlobal("crypto", { randomUUID: () => "00000000-0000-4000-8000-000000000001" });
});

it("sends an exact report-basis mutation with idempotency and correlation headers", async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ report_id: "r", report_version: 3, draft_revision_id: "d", provenance: [] }), { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
  const payload = { expected_version: 2, expected_draft_revision_id: "old", selections: [], rationale: "reviewed" };
  await api.reviseReportStandardsBasis("report/one", payload);
  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toBe("/technical-reports/report%2Fone/standards-basis-revisions");
  expect(init.method).toBe("POST");
  expect(new Headers(init.headers).get("Idempotency-Key")).toBeTruthy();
  expect(new Headers(init.headers).get("X-Correlation-ID")).toBeTruthy();
  expect(JSON.parse(init.body)).toEqual(payload);
});

it.each([[401, "protected"], [403, "protected"], [404, "protected"], [409, "conflict"], [422, "invalid"], [503, "unavailable"]] as const)("maps HTTP %s to the closed %s state", async (status, state) => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status })));
  await expect(api.standardsIntelligenceRun(7, "run-1")).resolves.toEqual({ state });
});
