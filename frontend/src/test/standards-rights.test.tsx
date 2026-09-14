import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OrganizationStandardsRightsPanel } from "../components/OrganizationStandardsRightsPanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: { standardRights: vi.fn(), replaceStandardRights: vi.fn(), revokeStandardRights: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));

const rights = { rights_binding_id: "rights-1", edition_id: "ed-1", source_provider_id: "licensed_provider", rights_basis: "organization_license", rights_status: "active", capabilities: { metadata_visibility: true, content_storage: false, indexing: false, excerpt_display: true, source_retrieval: true, derived_retention: false, derived_current_use: false }, ai_processing_permission: "approved_processor", approved_processor_policy_ids: ["policy-1"], effective_from: "2026-01-01T00:00:00Z", effective_until: null, version: 4, rights_digest: "b".repeat(64) };

beforeEach(() => { vi.restoreAllMocks(); apiMock.standardRights.mockReset().mockResolvedValue({ state: "success", data: { items: [rights], next_cursor: null } }); apiMock.replaceStandardRights.mockReset(); apiMock.revokeStandardRights.mockReset(); });

it("shows independent rights and replaces only the exact current version", async () => {
  vi.spyOn(window, "confirm").mockReturnValue(true);
  apiMock.replaceStandardRights.mockResolvedValue({ state: "success", data: { ...rights, version: 5 } });
  const user = userEvent.setup(); render(<OrganizationStandardsRightsPanel />);
  expect((await screen.findAllByText("Permitted")).length).toBe(3);
  await user.click(screen.getByRole("button", { name: "Replace rights" }));
  await user.type(screen.getByLabelText("Rights authority reference"), "contract-2026");
  await user.type(screen.getByLabelText("Rights authority SHA-256 digest"), "c".repeat(64));
  await user.click(screen.getByRole("button", { name: "Confirm replacement" }));
  await waitFor(() => expect(apiMock.replaceStandardRights).toHaveBeenCalledWith("ed-1", "licensed_provider", expect.objectContaining({ expected_version: 4, rights_authority_reference: "contract-2026", approved_processor_policy_ids: ["policy-1"] })));
  expect(apiMock.replaceStandardRights.mock.calls[0][2]).not.toHaveProperty("organization_id");
});

it("requires Human rationale and version confirmation to revoke", async () => {
  vi.spyOn(window, "prompt").mockReturnValue("license withdrawn"); vi.spyOn(window, "confirm").mockReturnValue(true);
  apiMock.revokeStandardRights.mockResolvedValue({ state: "success", data: { ...rights, rights_status: "revoked", version: 5 } });
  const user = userEvent.setup(); render(<OrganizationStandardsRightsPanel />);
  await user.click(await screen.findByRole("button", { name: "Revoke rights" }));
  expect(apiMock.revokeStandardRights).toHaveBeenCalledWith("rights-1", { expected_version: 4, reason: "license withdrawn" });
});
