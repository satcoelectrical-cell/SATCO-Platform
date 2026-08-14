import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { DashboardPage } from "../pages/DashboardPage";
import { LAYOUT_KEY } from "../dashboard/layout";

vi.mock("../api/client", () => ({ api: { projects: vi.fn().mockResolvedValue({ state: "success", data: { items: [], total: 0, page: 1, size: 20 } }) } }));

describe("customizable dashboard", () => {
  beforeEach(() => localStorage.clear());
  it("renders an operational default without fake counts", async () => { render(<MemoryRouter><DashboardPage /></MemoryRouter>); expect(screen.getByRole("heading", { name: /good work starts/i })).toBeVisible(); expect(screen.getByRole("heading", { name: "Active Projects" })).toBeVisible(); expect(await screen.findByText("No visible projects")).toBeVisible(); expect(screen.queryByText(/99|1,000/)).not.toBeInTheDocument(); });
  it("supports keyboard-accessible reorder, resize, hide, restore and reset", async () => { const user = userEvent.setup(); render(<MemoryRouter><DashboardPage /></MemoryRouter>); await user.click(screen.getByRole("button", { name: "Customize Dashboard" })); await user.click(screen.getByRole("button", { name: "Move Active Projects later" })); await user.selectOptions(screen.getByRole("combobox", { name: "Size of Active Projects" }), "wide"); await user.click(screen.getByRole("button", { name: "Hide Active Projects" })); expect(screen.queryByRole("heading", { name: "Active Projects" })).not.toBeInTheDocument(); await user.click(screen.getByRole("button", { name: "Active Projects" })); expect(screen.getByRole("heading", { name: "Active Projects" })).toBeVisible(); expect(localStorage.getItem(LAYOUT_KEY)).toBeTruthy(); await user.click(screen.getByRole("button", { name: /reset satco default/i })); expect(localStorage.getItem(LAYOUT_KEY)).toBeNull(); });
});
