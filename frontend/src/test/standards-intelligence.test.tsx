import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StandardsIntelligencePanel } from "../components/StandardsIntelligencePanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: { standardsIntelligence: vi.fn(), standardsIntelligenceOptions: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));
beforeEach(()=>apiMock.standardsIntelligenceOptions.mockResolvedValue({state:"success",data:{snapshots:[{handle:"snap-1",label:"provider — clause 1",availability_status:"available"},{handle:"snap-2",label:"provider — clause 2",availability_status:"available"}],assertions:[{handle:"assert-1",snapshot_handle:"snap-1",label:"requirement — clause 1",verification_status:"human_verified"}]}}));

it("preserves deterministic evidence and labels provider suggestions advisory-only", async () => {
  apiMock.standardsIntelligence.mockResolvedValue({ state: "success", data: { run_id: "run-1", project_id: 7, deterministic: { applicable_count: "2", rights_state: "permitted" }, deterministic_result_digest: "a".repeat(64), result_status: "completed", phase_status: "completed", advisory: { suggestions: [{ handle: "suggestion-1", rationale_code: "review_clause", advisory: "Review coordination clause." }], advisory_only: true, human_authority_required: true }, failure_code: null, advisory_only: true, human_authority_required: true } });
  const user = userEvent.setup(); render(<StandardsIntelligencePanel projectId={7} />);
  await user.type(screen.getByLabelText("Human advisory purpose"), "Check coordination gaps");
  await user.click(await screen.findByLabelText(/provider — clause 2/)); await user.click(screen.getByLabelText(/provider — clause 1/));
  await user.click(screen.getByLabelText(/requirement — clause 1/));
  await user.click(screen.getByRole("button", { name: "Run advisory check" }));
  expect(apiMock.standardsIntelligence).toHaveBeenCalledWith(7, { purpose: "Check coordination gaps", snapshot_ids: ["snap-2", "snap-1"], assertion_ids: ["assert-1"] });
  expect(await screen.findByText("Deterministic result retained independently of AI.")).toBeVisible();
  expect(screen.getByText(/Advisory only; Human review is required/)).toBeVisible();
});

it("shows a closed not-permitted outcome without unsafe advisory detail", async () => {
  apiMock.standardsIntelligence.mockResolvedValue({ state: "success", data: { run_id: "run-2", project_id: 7, deterministic: { rights_state: "prohibited" }, deterministic_result_digest: "b".repeat(64), result_status: "not_permitted", phase_status: "terminal", advisory: null, failure_code: "rights_prohibited", advisory_only: true, human_authority_required: true } });
  const user = userEvent.setup(); render(<StandardsIntelligencePanel projectId={7} />);
  await user.type(screen.getByLabelText("Human advisory purpose"), "Check rights"); await user.click(await screen.findByLabelText(/provider — clause 1/)); await user.click(screen.getByRole("button", { name: "Run advisory check" }));
  expect(await screen.findByText(/AI processing is not permitted/)).toBeVisible();
  expect(screen.queryByLabelText("Advisory suggestions")).not.toBeInTheDocument();
});

it("clears stale advisory data and moves focus to a closed conflict status", async () => {
  apiMock.standardsIntelligence
    .mockResolvedValueOnce({ state: "success", data: { run_id: "run-3", project_id: 7, deterministic: { rights_state: "permitted" }, deterministic_result_digest: "c".repeat(64), result_status: "completed_with_suggestions", phase_status: "terminal", advisory: { suggestions: [{ handle: "suggestion-1", rationale_code: "review_clause", advisory: "Review coordination clause." }], advisory_only: true, human_authority_required: true }, failure_code: null, advisory_only: true, human_authority_required: true } })
    .mockResolvedValueOnce({ state: "conflict" });
  const user = userEvent.setup(); render(<StandardsIntelligencePanel projectId={7} />);
  await user.type(screen.getByLabelText("Human advisory purpose"), "Check coordination gaps");
  await user.click(await screen.findByLabelText(/provider — clause 1/));
  await user.click(screen.getByRole("button", { name: "Run advisory check" }));
  expect(await screen.findByText("Review coordination clause.")).toBeVisible();
  await user.click(screen.getByRole("button", { name: "Run advisory check" }));
  const status = await screen.findByRole("status");
  expect(status).toHaveTextContent("no second provider call was attempted");
  expect(status).toHaveFocus();
  expect(screen.queryByText("Review coordination clause.")).not.toBeInTheDocument();
});
