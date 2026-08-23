import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SupportingEvidencePanel } from "../components/SupportingEvidencePanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: {
  supportingFiles: vi.fn(), evidence: vi.fn(), uploadSupportingFile: vi.fn(),
  linkSupportingFiles: vi.fn(), downloadSupportingFile: vi.fn(),
} }));
vi.mock("../api/client", () => ({ api: apiMock }));

const asset = {
  id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", organization_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  project_id: 7, workspace_id: 9, safe_filename: "very-long-protection-calculation-basis.pdf",
  media_type: "application/pdf", byte_size: 1024, digest_algorithm: "sha256",
  content_digest: "c".repeat(64), lifecycle: "available", version: 2,
  uploader_id: 11, uploaded_at: "2026-08-23T10:00:00Z", scanned_at: "2026-08-23T10:01:00Z",
  predecessor_asset_id: null, allowed_actions: ["download", "withdraw"],
};
const evidence = {
  id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd", organization_id: asset.organization_id,
  project_id: 7, workspace_id: 9, lifecycle: "proposed", source_kind: "engineering_record",
  source_reference: "field", source_revision: "r1", source_standing: "current",
  effective_at: null, supported_fact: "Verified relay setting basis", creator_id: 11,
  version: 1, created_at: "2026-08-23T10:00:00Z", updated_at: "2026-08-23T10:00:00Z",
  allowed_actions: ["link_supporting_files"],
};

beforeEach(() => {
  for (const fn of Object.values(apiMock)) fn.mockReset();
  apiMock.supportingFiles.mockResolvedValue({ state: "success", data: { items: [asset], visible_count: 1, continuation: null } });
  apiMock.evidence.mockResolvedValue({ state: "success", data: { items: [evidence], total: 1, page: 1, size: 100 } });
});

it("uploads real bytes and links only the exact server-returned available Asset", async () => {
  apiMock.uploadSupportingFile.mockResolvedValue({ state: "success", data: { ...asset, lifecycle: "quarantined" } });
  apiMock.linkSupportingFiles.mockResolvedValue({ state: "success", data: { ...evidence, version: 2 } });
  const user = userEvent.setup(); render(<SupportingEvidencePanel projectId={7} workspaceId={9} />);
  expect(await screen.findByText(asset.safe_filename)).toBeVisible();
  expect(screen.getByText(/not accepted engineering knowledge/i)).toBeVisible();
  const file = new File(["%PDF-1.7\nreal"], "relay-basis.pdf", { type: "application/pdf" });
  await user.upload(screen.getByLabelText("Supporting file"), file);
  await user.type(screen.getByLabelText("Upload rationale"), "Human-selected relay basis");
  fireEvent.submit(screen.getByLabelText("Supporting file").closest("form")!);
  await waitFor(() => expect(apiMock.uploadSupportingFile).toHaveBeenCalledWith(7, 9, file, "Human-selected relay basis"));

  await user.click(screen.getByLabelText(`Select ${asset.safe_filename} for Evidence`));
  await user.selectOptions(screen.getByLabelText("Proposed Evidence"), evidence.id);
  await user.type(screen.getByLabelText("Link rationale"), "Exact source supports the proposed fact");
  await user.click(screen.getByRole("button", { name: /link exact set/i }));
  await waitFor(() => expect(apiMock.linkSupportingFiles).toHaveBeenCalledWith(evidence.id, 1, [asset.id], "Exact source supports the proposed fact"));
  expect(screen.queryByLabelText(/organization id|asset id|project id|workspace id/i)).not.toBeInTheDocument();
});

it("uses truthful empty and protected states without fabricated file counts", async () => {
  apiMock.supportingFiles.mockResolvedValueOnce({ state: "protected" });
  render(<SupportingEvidencePanel projectId={7} workspaceId={9} />);
  expect(await screen.findByText("Not available")).toBeVisible();
  expect(screen.queryByText(/0 hidden|denied count|sample file/i)).not.toBeInTheDocument();
});
