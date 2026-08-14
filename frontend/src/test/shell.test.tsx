import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/AppShell";

vi.mock("../auth/AuthProvider", () => ({ useAuth: () => ({ logout: vi.fn(), status: "authenticated" }) }));

it("exposes only supported authenticated product navigation", () => { render(<MemoryRouter><Routes><Route element={<AppShell />}><Route index element={<div>Dashboard body</div>} /></Route></Routes></MemoryRouter>); expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible(); for (const name of ["Dashboard", "Projects", "Engineering Workspace", "Technical Reports", "Organizational Memory", "AI Capture Assistant"]) expect(screen.getByRole("link", { name: new RegExp(name, "i") })).toBeVisible(); expect(screen.queryByRole("link", { name: /notifications|settings|admin/i })).not.toBeInTheDocument(); expect(screen.getByText(/authenticated · organization context/i)).toBeVisible(); });
