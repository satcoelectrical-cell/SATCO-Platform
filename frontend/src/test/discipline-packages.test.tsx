import { render, screen } from "@testing-library/react";
import { trustedDisciplinePackageComponent } from "../disciplinePackages/components";

it("fails closed for untrusted package frontend component keys", () => {
  expect(trustedDisciplinePackageComponent("unknown.remote.component")).toBeNull();
  expect(trustedDisciplinePackageComponent("__proto__")).toBeNull();
});

it("does not render a component for an untrusted frontend contribution", () => {
  const Component = trustedDisciplinePackageComponent("customer.supplied.key");
  render(<>{Component ? <Component /> : <span>not rendered</span>}</>);
  expect(screen.getByText("not rendered")).toBeVisible();
});
