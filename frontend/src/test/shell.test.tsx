import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/AppShell";

vi.mock("../auth/AuthProvider", () => ({ useAuth: () => ({ logout: vi.fn(), status: "authenticated" }) }));

it("exposes only supported authenticated product navigation", () => { render(<MemoryRouter><Routes><Route element={<AppShell />}><Route index element={<div>Dashboard body</div>} /></Route></Routes></MemoryRouter>); expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible(); for (const name of ["Dashboard", "Projects", "Engineering Workspace", "Technical Reports", "Organizational Memory", "AI Capture Assistant"]) expect(screen.getByRole("link", { name: new RegExp(name, "i") })).toBeVisible(); expect(screen.queryByRole("link", { name: /notifications|settings|admin/i })).not.toBeInTheDocument(); expect(screen.getByText(/authenticated · organization context/i)).toBeVisible(); });

it("operates the navigation drawer by keyboard and restores focus on close", async () => {
  const user = userEvent.setup();
  render(<MemoryRouter><Routes><Route element={<AppShell />}><Route index element={<h1>Dashboard body</h1>} /></Route></Routes></MemoryRouter>);
  const trigger = screen.getByRole("button", { name: "Open navigation" });
  await user.click(trigger);
  expect(trigger).toHaveAttribute("aria-expanded", "true");
  const sidebar = within(screen.getByRole("complementary", { name: "Application sidebar" }));
  const close = sidebar.getByRole("button", { name: "Close navigation" });
  expect(close).toHaveFocus();
  await user.tab({ shift: true });
  expect(sidebar.getByRole("button", { name: "Sign out" })).toHaveFocus();
  await user.tab();
  expect(close).toHaveFocus();
  await user.keyboard("{Escape}");
  await waitFor(() => expect(trigger).toHaveFocus());
  expect(trigger).toHaveAttribute("aria-expanded", "false");
});

it("moves focus to the named main landmark after product navigation", async () => {
  const user = userEvent.setup();
  render(<MemoryRouter><Routes><Route element={<AppShell />}><Route index element={<h1>Dashboard body</h1>} /><Route path="projects" element={<h1>Projects body</h1>} /></Route></Routes></MemoryRouter>);
  await user.click(screen.getByRole("link", { name: /^Projects$/i }));
  expect(await screen.findByRole("heading", { name: "Projects body" })).toBeVisible();
  expect(screen.getByRole("main", { name: "Projects content" })).toHaveFocus();
});
