import { render, screen } from "@testing-library/react";
import { trustedDisciplinePackageComponent } from "../disciplinePackages/components";

it("uses exactly the three compiled package components and no unknown component", () => {
  for (const key of ["workspace.electrical.v1", "workspace.instrumentation.v1", "workspace.control_automation.v1"]) {
    const Component = trustedDisciplinePackageComponent(key);
    expect(Component).not.toBeNull();
  }
  expect(trustedDisciplinePackageComponent("customer.uploaded.component")).toBeNull();
});

it.each([
  ["workspace.electrical.v1"],
  ["workspace.instrumentation.v1"],
  ["workspace.control_automation.v1"],
  ["workspace.electrical.v1", "workspace.instrumentation.v1"],
  ["workspace.electrical.v1", "workspace.control_automation.v1"],
  ["workspace.instrumentation.v1", "workspace.control_automation.v1"],
  ["workspace.electrical.v1", "workspace.instrumentation.v1", "workspace.control_automation.v1"],
])("renders every server-authorized component in accepted combination %j", (...keys: string[]) => {
  render(<>{keys.map((key, index) => {
    const Component = trustedDisciplinePackageComponent(key);
    return Component ? <Component key={key} state="OPERATIONAL_AVAILABLE" projectId={101} workspaceId={201 + index} /> : null;
  })}</>);
  expect(screen.getAllByRole("region")).toHaveLength(keys.length);
  expect(screen.getAllByRole("button", { name: "Create atomic Object + Identifier" })).toHaveLength(keys.length);
});

it("keeps Batch-1 package shells unavailable or historical without an operational action", () => {
  const Component = trustedDisciplinePackageComponent("workspace.electrical.v1");
  render(Component ? <Component /> : null);
  expect(screen.getByRole("status")).toHaveTextContent("Package capability is unavailable.");
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});

it("renders the finite Instrumentation workflow only for server operational state", () => {
  const Component = trustedDisciplinePackageComponent("workspace.instrumentation.v1");
  const { rerender } = render(
    Component ? <Component state="OPERATIONAL_AVAILABLE" projectId={101} workspaceId={202} /> : null,
  );
  expect(screen.getByRole("region", { name: "Instrumentation V1" })).toHaveAttribute(
    "data-package-state", "OPERATIONAL_AVAILABLE",
  );
  expect(screen.getByRole("heading", { name: "Objects · 8" })).toBeInTheDocument();
  expect(screen.getAllByText("instrument loop")).toHaveLength(2);
  expect(screen.getByText("connected to io channel")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Create atomic Object + Identifier" })).toBeEnabled();

  rerender(Component ? <Component state="HISTORICAL_READ_ONLY" projectId={101} workspaceId={202} /> : null);
  expect(screen.getByRole("status")).toHaveTextContent("read-only");
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});

it("keeps indeterminate Instrumentation state non-authoritative", () => {
  const Component = trustedDisciplinePackageComponent("workspace.instrumentation.v1");
  render(Component ? <Component state="INDETERMINATE" projectId={101} workspaceId={202} /> : null);
  expect(screen.getByRole("region", { name: "Instrumentation V1" })).toHaveAttribute("aria-busy", "true");
  expect(screen.getByRole("status")).toHaveTextContent("unavailable");
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});

it("renders the exact Control & Automation workflow only for server operational state", () => {
  const Component = trustedDisciplinePackageComponent("workspace.control_automation.v1");
  const { rerender } = render(
    Component ? <Component state="OPERATIONAL_AVAILABLE" projectId={101} workspaceId={202} /> : null,
  );
  expect(screen.getByRole("region", { name: "Control & Automation V1" })).toHaveAttribute(
    "data-package-state", "OPERATIONAL_AVAILABLE",
  );
  expect(screen.getByRole("heading", { name: "Objects · 7" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Relationships · 13" })).toBeInTheDocument();
  expect(screen.getAllByText("io channel")).toHaveLength(2);
  expect(screen.getAllByText("participates in sequence")).toHaveLength(2);
  expect(screen.getAllByText("cause effect matrix")).toHaveLength(2);
  expect(screen.getByText("io logic connectivity")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Create atomic Object + Identifier" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Create governed Relationship" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Bind Context declaration" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Bind Evidence declaration" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Create package Deliverable" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Evaluate exact readiness" })).toBeEnabled();

  rerender(Component ? <Component state="HISTORICAL_READ_ONLY" projectId={101} workspaceId={202} /> : null);
  expect(screen.getByRole("status")).toHaveTextContent("read-only");
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});

it("keeps indeterminate Control & Automation state non-authoritative", () => {
  const Component = trustedDisciplinePackageComponent("workspace.control_automation.v1");
  render(Component ? <Component state="INDETERMINATE" projectId={101} workspaceId={202} /> : null);
  expect(screen.getByRole("region", { name: "Control & Automation V1" })).toHaveAttribute("aria-busy", "true");
  expect(screen.getByRole("status")).toHaveTextContent("unavailable");
  expect(screen.queryByRole("button")).not.toBeInTheDocument();
});
