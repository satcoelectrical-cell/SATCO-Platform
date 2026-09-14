import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { EngineeringGuidancePanel } from "../components/EngineeringGuidancePanel";
import type { EngineeringGuidanceResult, GuidanceSafeEvidence } from "../api/types";

const { apiMock } = vi.hoisted(() => ({ apiMock: { engineeringGuidance: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));

const guidanceTypes = ["engineering_observation", "missing_engineering_consideration", "potential_risk_consideration", "explicit_conflict_to_verify", "verification_point", "clarification_requirement", "suggested_next_check", "alternative_consideration"] as const;
const evidenceStates = ["sufficient", "partial", "insufficient", "indeterminate"] as const;
const aiStates = ["not_requested", "available", "disabled", "unavailable", "timed_out", "rejected"] as const;
const categories = ["instrumentation_measurement", "electrical_power_or_interconnection", "automation_and_control"] as const;

function evidence(safe_key: string, visible_label: string | null = null, predicate_code = "internal.predicate"): GuidanceSafeEvidence {
  return { reference_kind: "visible_fact", safe_key, predicate_code, observed_at: "2026-08-27T00:00:00Z", visible_label };
}

function result(kind: "success" | "partial_success" = "success"): EngineeringGuidanceResult {
  return {
    kind,
    observation: {
      catalog: { catalog_id: "engineering_guidance.v1", catalog_version: 1, catalog_digest: "catalog-digest", rules: [] },
      context_observation_digest: "context-digest",
      status: kind === "partial_success" ? "partial" : "complete_within_bounds",
      source_observation_started_at: "2026-08-27T00:00:00Z",
      source_observation_completed_at: "2026-08-27T00:00:01Z",
      generated_at: "2026-08-27T00:00:02Z",
      limitations: ["Bounded observation"],
      authority_class: "derived",
      advisory: true,
      authoritative: false,
      no_guidance_warranted: false,
      items: guidanceTypes.map((guidance_type, ordinal) => {
        const aiState = aiStates[ordinal % aiStates.length];
        return {
        guidance_item_id: `item-${ordinal}`,
        catalog_id: "engineering_guidance.v1",
        catalog_version: 1,
        catalog_digest: "catalog-digest",
        rule_id: `rule-${ordinal}`,
        rule_version: 1,
        ordinal,
        guidance_type,
        title: `Guidance ${ordinal}`,
        summary: `Summary ${ordinal}`,
        explanation: `Explanation ${ordinal}`,
        engineering_rationale: `Engineering rationale ${ordinal}`,
        evidence_sufficiency: evidenceStates[ordinal % evidenceStates.length],
        evidence: [evidence(`engineering_object:fixture-selector-${ordinal}`)],
        assumptions: [`Assumption ${ordinal}`],
        limitations: [`Limitation ${ordinal}`],
        verification_requirements: [`Verify ${ordinal}`],
        source_observation_started_at: "2026-08-27T00:00:00Z",
        source_observation_completed_at: "2026-08-27T00:00:01Z",
        generated_at: "2026-08-27T00:00:02Z",
        authority_class: "derived",
        advisory: true,
        authoritative: false,
        ai_enhancement: aiState === "available" ? { state: aiState, enhanced_explanation: "Model-assisted explanation text", enhanced_clarification: null } : { state: aiState, enhanced_explanation: null, enhanced_clarification: null },
      };
      }),
      candidate_material_requirements: categories.map((category, ordinal) => ({
        candidate_id: `candidate-${ordinal}`,
        category,
        triggering_guidance_item_id: `item-${ordinal}`,
        triggering_rule_id: `rule-${ordinal}`,
        engineering_rationale: `Candidate rationale ${ordinal}`,
        evidence: [evidence(`engineering_object:candidate-selector-${ordinal}`)],
        attributes_to_determine: [{ key: `attribute-${ordinal}`, label: `Attribute ${ordinal}`, status: "requires_engineering_determination" }],
        assumptions: [`Candidate assumption ${ordinal}`],
        limitations: [`Candidate limitation ${ordinal}`],
        verification_requirements: [`Candidate verify ${ordinal}`],
        evidence_sufficiency: evidenceStates[ordinal],
        quantity_status: "not_estimated",
        generated_at: "2026-08-27T00:00:02Z",
        authority_class: "derived",
        advisory: true,
        authoritative: false,
      })),
    },
  };
}

function noGuidanceResult(kind: "success" | "partial_success" = "success"): EngineeringGuidanceResult {
  const populated = result(kind);
  if (populated.kind !== "success" && populated.kind !== "partial_success") throw new Error("success fixture required");
  return { ...populated, observation: { ...populated.observation, no_guidance_warranted: true, items: [], candidate_material_requirements: [] } };
}

beforeEach(() => apiMock.engineeringGuidance.mockReset());

it("renders the eight bounded guidance types, three advisory candidate categories, and server classifications", async () => {
  apiMock.engineeringGuidance.mockResolvedValue({ state: "success", data: result("partial_success") });
  render(<EngineeringGuidancePanel projectId={7} workspaceId={9} />);
  expect(await screen.findByRole("heading", { name: "Engineering Guidance" })).toBeVisible();
  expect(apiMock.engineeringGuidance).toHaveBeenCalledWith(7, { workspace_id: 9, ai_enhancement: "not_requested" });
  for (const type of guidanceTypes) expect(screen.getAllByText(type.replaceAll("_", " "), { exact: false }).length).toBeGreaterThan(0);
  for (const category of categories) expect(screen.getAllByText(category.replaceAll("_", " "), { exact: false }).length).toBeGreaterThan(0);
  expect(screen.getAllByText("Quantity: NOT ESTIMATED")).toHaveLength(3);
  expect(screen.getByText(/Derived, advisory and non-authoritative/)).toBeVisible();
  expect(screen.getByText("Partial bounded observation")).toBeVisible();
  expect(screen.getAllByText("Model-assisted explanation text").length).toBeGreaterThan(0);
});

it("renders server evidence in order without exposing safe keys or reconstructing candidate evidence", async () => {
  const data = result();
  if (data.kind !== "success" && data.kind !== "partial_success") throw new Error("success fixture required");
  const observation = data.observation;
  const executionSelector = "6a5b4c3d-2e1f-4a5b-8c9d-0e1f2a3b4c5d";
  const deliverableSelector = "2b3c4d5e-6a7b-4c8d-9e0f-1a2b3c4d5e6f";
  const objectSelector = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d";
  const unknownKey = "unrecognized:opaque-selector";
  observation.items[0].evidence = [
    evidence("project_control:risk", null, "project_control.risk"),
    evidence("project_control:issue", null, "project_control.issue"),
    evidence("project_control:change", null, "change.confirmed_impact"),
    evidence(`execution:${executionSelector}`, "Authorized execution label"),
    evidence(`deliverable:${deliverableSelector}`, ""),
    evidence(`engineering_object:${objectSelector}`, "Authorized object label"),
    evidence("project_control:risk", null, "duplicate.project_control.risk"),
    evidence(unknownKey, null, "unknown.internal.predicate"),
  ];
  observation.items[1].evidence = [evidence(`execution:${executionSelector}`, " \t ")];
  observation.items[3].evidence = [];
  observation.candidate_material_requirements[0].evidence = [evidence("engineering_object:candidate-only-selector")];
  observation.candidate_material_requirements[1].evidence = [];
  observation.candidate_material_requirements[2].evidence = [evidence("project_control:change")];
  apiMock.engineeringGuidance.mockResolvedValue({ state: "success", data });

  render(<EngineeringGuidancePanel projectId={7} />);
  await screen.findByRole("heading", { name: "Engineering Guidance" });

  const guidanceArticle = screen.getByRole("heading", { name: "Guidance 0" }).closest("article");
  expect(guidanceArticle).not.toBeNull();
  expect(within(guidanceArticle!).getAllByRole("listitem").slice(0, 8).map((item) => item.textContent)).toEqual([
    "Project Control — Risk",
    "Project Control — Issue",
    "Project Control — Change",
    "Execution — Authorized execution label",
    "Deliverable",
    "Engineering Object — Authorized object label",
    "Project Control — Risk",
    "Authorized supporting evidence",
  ]);
  expect(within(screen.getByRole("heading", { name: "Guidance 1" }).closest("article")!).getByText("Execution")).toBeVisible();
  expect(within(screen.getByRole("heading", { name: "Guidance 3" }).closest("article")!).getByText("No safe evidence reference supplied.")).toBeVisible();

  const candidateArticle = screen.getByText("Candidate rationale 0").closest("article");
  expect(candidateArticle).not.toBeNull();
  expect(within(candidateArticle!).getByText("Engineering Object")).toBeVisible();
  expect(within(screen.getByText("Candidate rationale 1").closest("article")!).getByText("No safe evidence reference supplied.")).toBeVisible();
  expect(within(screen.getByText("Candidate rationale 2").closest("article")!).getByText("Project Control — Change")).toBeVisible();

  for (const hidden of ["project_control:risk", executionSelector, deliverableSelector, objectSelector, unknownKey, "project_control.risk", "change.confirmed_impact", "unknown.internal.predicate", "2026-08-27T00:00:00Z"]) expect(screen.queryByText(hidden, { exact: false })).not.toBeInTheDocument();
  expect(screen.getAllByText("Quantity: NOT ESTIMATED")).toHaveLength(3);
  expect(screen.getByText(/not a BOM, MTO, BOQ, requisition, selection, or purchase item/)).toBeVisible();
});

it("requests optional AI only after explicit Human action and does not treat it as authoritative", async () => {
  apiMock.engineeringGuidance.mockResolvedValue({ state: "success", data: result() });
  const user = userEvent.setup();
  render(<EngineeringGuidancePanel projectId={7} />);
  await screen.findByRole("heading", { name: "Engineering Guidance" });
  expect(apiMock.engineeringGuidance).toHaveBeenCalledTimes(1);
  await user.click(screen.getByRole("button", { name: "Request optional AI enhancement" }));
  expect(apiMock.engineeringGuidance).toHaveBeenLastCalledWith(7, { workspace_id: null, ai_enhancement: "requested" });
  expect(screen.queryByRole("button", { name: /select|purchase|requisition/i })).not.toBeInTheDocument();
});

it("keeps protected, unavailable, and insufficient results payload-safe", async () => {
  apiMock.engineeringGuidance.mockResolvedValueOnce({ state: "success", data: { kind: "protected_not_found" } });
  const { rerender } = render(<EngineeringGuidancePanel projectId={7} />);
  expect(await screen.findByText("Not available")).toBeVisible();
  expect(screen.queryByText(/protected_not_found|denied|forbidden/i)).not.toBeInTheDocument();
  apiMock.engineeringGuidance.mockResolvedValueOnce({ state: "success", data: { kind: "insufficient_context" } });
  rerender(<EngineeringGuidancePanel projectId={8} />);
  expect(await screen.findByText("More authorized context is needed")).toBeVisible();
  apiMock.engineeringGuidance.mockResolvedValueOnce({ state: "success", data: { kind: "unavailable" } });
  rerender(<EngineeringGuidancePanel projectId={9} />);
  expect(await screen.findByText(/temporarily unavailable/i)).toBeVisible();
});

it("uses the authoritative no-guidance boolean, preserves partial limitations, and suppresses AI", async () => {
  apiMock.engineeringGuidance.mockResolvedValue({ state: "success", data: noGuidanceResult("partial_success") });
  render(<EngineeringGuidancePanel projectId={7} />);
  expect(await screen.findByText("No guidance warranted")).toBeVisible();
  expect(screen.getByText("Partial bounded observation")).toBeVisible();
  expect(screen.getByText("Bounded observation")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Request optional AI enhancement" })).not.toBeInTheDocument();
  expect(screen.queryByText("More authorized context is needed")).not.toBeInTheDocument();
});
