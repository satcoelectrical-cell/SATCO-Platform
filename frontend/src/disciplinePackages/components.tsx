import type { ComponentType } from "react";

/** Trusted compiled key map only; server metadata never supplies executable code. */
const components: Readonly<Record<string, ComponentType>> = Object.freeze({});

export function trustedDisciplinePackageComponent(key: string): ComponentType | null {
  return Object.prototype.hasOwnProperty.call(components, key) ? components[key] : null;
}
