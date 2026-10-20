import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProjectStandardsPanel } from "../components/ProjectStandardsPanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: { projectStandards: vi.fn(), projectStandardCandidates: vi.fn(), standardsSelectorOptions:vi.fn(), declareProjectStandard: vi.fn(), retireProjectStandard: vi.fn(), retrieveStandardSources: vi.fn(), displayStandardSource: vi.fn(), createStandardAssertion: vi.fn(), decideStandardAssertion: vi.fn(), standards: vi.fn(), standard: vi.fn(), standardRights: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));

beforeEach(() => {
  for (const fn of Object.values(apiMock)) fn.mockReset();
  apiMock.projectStandards.mockResolvedValue({ state: "success", data: { items: [], next_cursor: null } });
  apiMock.standards.mockResolvedValue({state:"success",data:{items:[{standard_id:"std-1",issuer:"IEC",designation:"61850"}],next_cursor:null}});
  apiMock.standard.mockResolvedValue({state:"success",data:{editions:[{edition_id:"ed-1",edition_designation:"2024"}]}});
  apiMock.standardRights.mockResolvedValue({state:"success",data:{items:[{rights_binding_id:"rb-1",edition_id:"ed-1",source_provider_id:"registry_metadata"}]}});
  apiMock.standardsSelectorOptions.mockResolvedValue({state:"success",data:{editions:[{handle:"ed-1",label:"IEC 61850 — 2024",current_revision:0}],rights:[{edition_handle:"ed-1",provider_handle:"registry_metadata",label:"Registry metadata",reference_allowed:true,material_support_allowed:true}]}});
  apiMock.projectStandardCandidates.mockResolvedValue({ state: "success", data: { items: [{ candidate_id: "cand-1", candidate_digest: "a".repeat(64), designation_key: "IEC-61850", suggested_role: "design_basis", rationale_code: "package_mapping", package_key: "electrical", package_version: "1.0", standard_edition_id: null }] } });
});

it("uses the selected edition's own applicability revision",async()=>{
  apiMock.standardsSelectorOptions.mockResolvedValue({state:"success",data:{editions:[{handle:"ed-1",label:"IEC 61850 — 2024",current_revision:1},{handle:"ed-2",label:"IEC 61850 — 2026",current_revision:7}],rights:[]}});
  apiMock.declareProjectStandard.mockResolvedValue({state:"success",data:{revision:8}});
  const user=userEvent.setup();render(<ProjectStandardsPanel projectId={7}/>);
  await user.selectOptions(await screen.findByLabelText("Registry edition"),"ed-2");await user.type(screen.getByLabelText("Human rationale"),"Selected current edition");await user.click(screen.getByRole("button",{name:"Record declaration"}));
  await waitFor(()=>expect(apiMock.declareProjectStandard).toHaveBeenCalledWith(7,expect.objectContaining({edition_id:"ed-2",expected_revision:7})));
});

it("keeps package candidates advisory and records an explicit Human applicability declaration", async () => {
  apiMock.declareProjectStandard.mockResolvedValue({ state: "success", data: { revision: 1 } });
  const user = userEvent.setup(); render(<ProjectStandardsPanel projectId={7} />);
  expect(await screen.findByText(/advisory only; resolve to registry metadata/i)).toBeVisible();
  await user.selectOptions(await screen.findByLabelText("Registry edition"), "ed-1");
  await user.type(screen.getByLabelText("Human rationale"), "Project design basis selected by engineer");
  await user.click(screen.getByRole("button", { name: "Record declaration" }));
  await waitFor(() => expect(apiMock.declareProjectStandard).toHaveBeenCalledWith(7, expect.objectContaining({ edition_id: "ed-1", expected_revision: 0, rationale_code: "human_review" })));
  expect(apiMock.declareProjectStandard.mock.calls[0][1]).not.toHaveProperty("organization_id");
});

it("requires attributable Human provenance for a mandatory declaration", async () => {
  apiMock.declareProjectStandard.mockResolvedValue({ state: "success", data: { revision: 1 } });
  const user = userEvent.setup(); render(<ProjectStandardsPanel projectId={7} />);
  await user.selectOptions(await screen.findByLabelText("Registry edition"), "ed-1");
  await user.selectOptions(screen.getByLabelText("Role"), "mandatory");
  await user.type(screen.getByLabelText("Human rationale"), "Contractual design requirement");
  await user.type(screen.getByLabelText("Authority reference"), "Contract clause 12");
  await user.type(screen.getByLabelText("Authority SHA-256 digest"), "d".repeat(64));
  await user.click(screen.getByRole("button", { name: "Record declaration" }));
  await waitFor(() => expect(apiMock.declareProjectStandard).toHaveBeenCalledWith(7, expect.objectContaining({ applicability_role: "mandatory", mandatory_source_kind: "contract", mandatory_source_reference: "Contract clause 12", mandatory_source_digest: "d".repeat(64) })));
});

it("separates governed retrieval, fresh display, assertion creation, and Human verification", async () => {
  const snapshot = { snapshot_id: "snap-1", edition_id: "ed-1", source_location: "clause-5", availability_status: "available", integrity_verified: true, snapshot_digest: "b".repeat(64), authorized_handle: "display-handle" };
  const assertion = { assertion_id: "assert-1", assertion_kind: "requirement_statement", assertion_digest: "c".repeat(64), verification_status: "unverified", version: 2, verification_handle: "verify-handle", rejection_handle: "reject-handle" };
  apiMock.retrieveStandardSources.mockResolvedValue({ state: "success", data: { items: [snapshot] } });
  apiMock.displayStandardSource.mockResolvedValue({ state: "success", data: { excerpt: "Authorized excerpt" } });
  apiMock.createStandardAssertion.mockResolvedValue({ state: "success", data: assertion });
  apiMock.decideStandardAssertion.mockResolvedValue({ state: "success", data: { ...assertion, verification_status: "human_verified", version: 3 } });
  vi.spyOn(window, "confirm").mockReturnValue(true);
  const user = userEvent.setup(); render(<ProjectStandardsPanel projectId={7} />);
  await user.selectOptions(await screen.findByLabelText("Registry edition"), "ed-1");
  await user.selectOptions(await screen.findByLabelText("Authorized source provider"), "registry_metadata");
  await user.type(screen.getByLabelText(/Provider-local locations/), "clause-5");
  await user.click(screen.getByRole("button", { name: "Create bounded snapshots" }));
  await user.click(await screen.findByRole("button", { name: "Freshly authorize display" }));
  expect(apiMock.displayStandardSource).toHaveBeenCalledWith(7, "snap-1", "display-handle");
  expect(await screen.findByText(/Authorized excerpt/)).toBeVisible();
  await user.type(screen.getByLabelText("Requirement statement"), "Equipment shall be interlocked.");
  await user.click(screen.getByRole("button", { name: "Record unverified assertion" }));
  await user.type(await screen.findByLabelText("Human decision rationale"), "Verified against current licensed text");
  await user.click(screen.getByRole("button", { name: "Verify assertion" }));
  expect(apiMock.decideStandardAssertion).toHaveBeenCalledWith(7, "assert-1", true, { expected_version: 2, reason: "Verified against current licensed text" }, "verify-handle");
});
