import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TechnicalReportStandardsBasisPanel } from "../components/TechnicalReportStandardsBasisPanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: { reportStandardCandidates: vi.fn(), reviseReportStandardsBasis: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));

const standard = { entry_id: "entry-standard", ordinal: 0, source_class: "standards_material", source_type: "standard", is_material: true, owning_capability: "standards", reliance_role: "source_standard", verification_status: "verified", availability_status: "available", origin_attribution: "IEC 61850:2024", limitations: [], locator: {}, integrity_algorithm: "sha256", integrity_digest: "a".repeat(64) };
const unrelatedSource = { ...standard, entry_id: "unrelated-source", source_type: "evidence", origin_attribution: "SHOULD NOT RENDER" };
const report = { id: "report-1", lifecycle: "draft", version: 7, draft_revision_id: "revision-1" } as never;
const candidate = { authorized_handle: "basis-handle", standard_identity_id: "std-1", edition_id: "ed-1", issuer: "IEC", designation: "61850", edition_designation: "2024", standing: "superseded", materiality: "reference_only", eligibility: "standing_acknowledgement_required", warnings: [] };

it("uses only canonical source_type standard and attaches an exact Human-selected revision", async () => {
  apiMock.reportStandardCandidates.mockResolvedValue({ state: "success", data: { items: [candidate] } });
  apiMock.reviseReportStandardsBasis.mockResolvedValue({ state: "success", data: {} });
  vi.spyOn(window, "confirm").mockReturnValue(true);
  const user = userEvent.setup(); render(<TechnicalReportStandardsBasisPanel provenance={[standard, unrelatedSource]} report={report} />);
  expect(screen.getByText("IEC 61850:2024")).toBeVisible();
  expect(screen.queryByText("SHOULD NOT RENDER")).not.toBeInTheDocument();
  await user.click(await screen.findByRole("checkbox"));
  await user.type(screen.getByLabelText("Human selection rationale"), "Needed for interface terminology");
  await user.type(screen.getByLabelText("Standing acknowledgement"), "Superseded standing reviewed");
  await user.type(screen.getByLabelText("Report revision rationale"), "Attach reviewed reference basis");
  await user.click(screen.getByRole("button", { name: "Attach to new exact revision" }));
  await waitFor(() => expect(apiMock.reviseReportStandardsBasis).toHaveBeenCalledWith("report-1", { expected_version: 7, expected_draft_revision_id: "revision-1", selections: [{ authorized_handle: "basis-handle", materiality: "reference_only", selection_rationale: "Needed for interface terminology", standing_acknowledgement: "Superseded standing reviewed", assertion_id: null }], rationale: "Attach reviewed reference basis" }));
});

it("masks unavailable historical origin while retaining non-sensitive integrity state", () => {
  render(<TechnicalReportStandardsBasisPanel provenance={[{ ...standard, availability_status: "not_available", origin_attribution: "Secret licensed title" }]} />);
  expect(screen.getByText("Protected historical standards basis")).toBeVisible();
  expect(screen.queryByText("Secret licensed title")).not.toBeInTheDocument();
});
