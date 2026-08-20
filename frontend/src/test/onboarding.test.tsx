import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { BootstrapPage, ActivatePage } from "../pages/OnboardingPages";

describe("governed onboarding", () => {
  beforeEach(() => { sessionStorage.clear(); vi.restoreAllMocks(); vi.stubGlobal("crypto", { randomUUID: () => "00000000-0000-4000-8000-000000000001" }); });

  it("keeps the platform bootstrap key out of the request body and shows a one-time credential", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ outcome: "success", one_time_token: "t".repeat(48) }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<MemoryRouter><BootstrapPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText(/platform bootstrap key/i), { target: { value: "k".repeat(40) } });
    fireEvent.change(screen.getByLabelText(/organization name/i), { target: { value: "Acme Engineering" } });
    fireEvent.change(screen.getByLabelText(/organization slug/i), { target: { value: "acme-engineering" } });
    fireEvent.change(screen.getByLabelText(/admin username/i), { target: { value: "acme-admin" } });
    fireEvent.change(screen.getByLabelText(/admin email/i), { target: { value: "admin@acme.example" } });
    fireEvent.click(screen.getByRole("button", { name: /create governed organization/i }));
    await screen.findByText(/copy this activation credential now/i);
    const [, init] = fetchMock.mock.calls[0];
    expect(new Headers(init.headers).get("X-SATCO-Bootstrap-Key")).toBe("k".repeat(40));
    expect(String(init.body)).not.toContain("k".repeat(40));
    expect(screen.getByText("t".repeat(48))).toBeVisible();
  });

  it("reports protected activation failure without internal detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ outcome: "invalid_request" }), { status: 200 })));
    render(<MemoryRouter initialEntries={["/activate"]}><ActivatePage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText(/one-time credential/i), { target: { value: "x".repeat(48) } });
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: "new-secure-password" } });
    fireEvent.click(screen.getByRole("button", { name: /activate account/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/not accepted/i));
    expect(screen.queryByText(/exception|database|user id/i)).not.toBeInTheDocument();
  });
});
