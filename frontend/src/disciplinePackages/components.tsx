import type { ComponentType } from "react";
import type { PackagePanelProps } from "./PackageWorkspaceShell";
import { ElectricalPackagePanel } from "./ElectricalPackagePanel";
import { InstrumentationPackagePanel } from "./InstrumentationPackagePanel";
import { ControlAutomationPackagePanel } from "./ControlAutomationPackagePanel";

/** Trusted compiled key map only; server metadata never supplies executable code. */
const components: Readonly<Record<string, ComponentType<PackagePanelProps>>> = Object.freeze({
  "workspace.electrical.v1": ElectricalPackagePanel,
  "workspace.instrumentation.v1": InstrumentationPackagePanel,
  "workspace.control_automation.v1": ControlAutomationPackagePanel,
});

export function trustedDisciplinePackageComponent(key: string): ComponentType<PackagePanelProps> | null {
  return Object.prototype.hasOwnProperty.call(components, key) ? components[key] : null;
}
