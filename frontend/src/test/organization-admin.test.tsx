import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { OrganizationAdminPage } from "../pages/OrganizationAdminPage";

vi.mock("../auth/AuthProvider", () => ({ useAuth: () => ({ profile: { role: "admin", organization: { id: "o", name: "Acme", slug: "acme" } } }) }));

it("shows only real server members and treats issued credentials as one-time", async () => {
  let provisioned = false;
  const members = () => ({ outcome: "success", items: provisioned ? [] : [{ user_id: 7, username: "engineer", email: "e@example.com", full_name: "Engineer", role: "engineer", account_active: true, activation_pending: false, membership_enabled: true, membership_selected: true, version: 1 }] });
  vi.stubGlobal("crypto", { randomUUID: () => "00000000-0000-4000-8000-000000000001" });
  vi.stubGlobal("fetch", vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    let data: unknown;
    if (url.endsWith("/organizations/current/standard-rights")) data = { items: [], next_cursor: null };
    else if (url.endsWith("/organizations/current/discipline-package-configuration")) data = { organization_id: "o", configuration_version: 0, enabled_selections: [], disabled_selections: [], registry_digest: "d".repeat(64), updated_at: null };
    else if (url.includes("/discipline-packages/supported")) data = { registry_digest: "d".repeat(64), items: [], next_cursor: null };
    else if (url.endsWith("/organization-admin/members") && init?.method === "POST") { provisioned = true; data = { outcome: "success", member: { user_id: 8 }, one_time_token: "z".repeat(48) }; }
    else data = members();
    return Promise.resolve(new Response(JSON.stringify(data), { status: 200 }));
  }));
  render(<MemoryRouter><OrganizationAdminPage /></MemoryRouter>);
  await screen.findByText("Engineer");
  expect(screen.queryByText(/sample|demo member/i)).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText(/^username$/i), { target: { value: "new-user" } });
  fireEvent.change(screen.getByLabelText(/^email$/i), { target: { value: "new@example.com" } });
  fireEvent.click(screen.getByRole("button", { name: /provision member/i }));
  await screen.findByText("z".repeat(48));
  expect(screen.getByText(/will not be shown again/i)).toBeVisible();
});
