import type { ReactNode } from "react";

export type PackageEffectiveState = "OPERATIONAL_AVAILABLE" | "HISTORICAL_READ_ONLY" | "INDETERMINATE" | "UNAVAILABLE";
export interface PackagePanelProps { state?: PackageEffectiveState; projectId?: number; workspaceId?: number }

export function PackageWorkspaceShell({
  title,
  state,
  children,
}: Readonly<{ title: string; state: PackageEffectiveState; children?: ReactNode }>) {
  const unavailable = state === "INDETERMINATE" || state === "UNAVAILABLE";
  const readOnly = state === "HISTORICAL_READ_ONLY";
  return (
    <section aria-label={title} data-package-state={state} aria-busy={state === "INDETERMINATE"}>
      <h2>{title}</h2>
      {unavailable ? <p role="status">Package capability is unavailable.</p> : null}
      {readOnly ? <p role="status">Historical package information is read-only.</p> : null}
      {!unavailable && !readOnly ? children : null}
    </section>
  );
}
