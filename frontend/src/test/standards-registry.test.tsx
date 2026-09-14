import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StandardsRegistryPanel } from "../components/StandardsRegistryPanel";

const { apiMock } = vi.hoisted(() => ({ apiMock: { standards: vi.fn(), standard: vi.fn() } }));
vi.mock("../api/client", () => ({ api: apiMock }));

const identity = { standard_id: "std-1", catalog_scope: "global_trusted", issuer: "IEC", designation: "61850", title: "Communication networks", identity_digest: "a".repeat(64), retired_from_new_selection: false };

it("searches metadata and opens authorized edition detail without implying applicability", async () => {
  apiMock.standards.mockResolvedValue({ state: "success", data: { items: [identity], next_cursor: null } });
  apiMock.standard.mockResolvedValue({ state: "success", data: { ...identity, editions: [{ edition_id: "ed-1", edition_designation: "2024", official_publication_identifier: "IEC 61850:2024", standing_history: [{ standing: "current", observed_effective_at: "2026-01-01T00:00:00Z", version: 1 }] }] } });
  const user = userEvent.setup(); render(<StandardsRegistryPanel />);
  await user.type(screen.getByLabelText("Search registry metadata"), "61850");
  await user.click(screen.getByRole("button", { name: "Search" }));
  expect(apiMock.standards).toHaveBeenCalledWith("61850");
  expect(await screen.findByText("Trusted global metadata")).toBeVisible();
  const detailButton = screen.getByRole("button", { name: "Open metadata detail" });
  detailButton.focus();
  await user.keyboard("{Enter}");
  const publication = await screen.findByText(/IEC 61850:2024/);
  expect(publication).toBeVisible();
  expect(publication.closest('[role="status"]')).toHaveFocus();
  expect(screen.getByLabelText("Standing history for 2024")).toHaveTextContent("current");
  expect(screen.getByText(/does not grant source-content rights/i)).toBeVisible();
});

it("collapses a denied detail to a neutral protected state", async () => {
  apiMock.standards.mockResolvedValue({ state: "success", data: { items: [identity], next_cursor: null } });
  apiMock.standard.mockResolvedValue({ state: "protected" });
  const user = userEvent.setup(); render(<StandardsRegistryPanel />);
  await user.click(screen.getByRole("button", { name: "Search" }));
  await user.click(await screen.findByRole("button", { name: "Open metadata detail" }));
  expect(await screen.findByText("This standards detail is not available.")).toBeVisible();
});
