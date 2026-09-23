import { render, screen } from "@testing-library/react";
import { EmptyState, ErrorState, LoadingState, ProtectedState } from "../components/States";

describe("integrated state semantics", () => {
  it("announces loading, empty and protected states without relying on color", () => {
    const { rerender } = render(<LoadingState label="Loading authorized Projects…" />);
    expect(screen.getByRole("status")).toHaveAttribute("data-state", "loading");
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    rerender(<EmptyState title="No visible Projects" detail="Create an authorized Project to continue." />);
    expect(screen.getByRole("status")).toHaveAttribute("data-state", "empty");
    expect(screen.getByText("No visible Projects")).toBeVisible();
    rerender(<ProtectedState />);
    expect(screen.getByRole("status")).toHaveAttribute("data-state", "protected");
    expect(screen.getByText(/outside your current authorized context/i)).toBeVisible();
  });

  it("announces unavailable failures while preserving neutral disclosure", () => {
    render(<ErrorState unavailable />);
    expect(screen.getByRole("alert")).toHaveAttribute("data-state", "unavailable");
    expect(screen.getByText("No protected details were disclosed.")).toBeVisible();
  });
});
