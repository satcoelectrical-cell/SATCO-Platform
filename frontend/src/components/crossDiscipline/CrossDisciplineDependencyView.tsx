import type { XDIFinding } from "../../api/types";

export function CrossDisciplineDependencyView({ findings }: { findings: XDIFinding[] | null }) {
  const applicable = findings?.filter((finding) => finding.subcode === "ei.cable_jb_path") ?? [];
  return <section className="cross-discipline-card cross-discipline-ei-card" aria-label="Electrical and instrumentation dependency">
    <h3>Cable/JB dependency</h3>
    <p className="cross-discipline-advisory">Only a persisted authorized path gap is displayed; topology is never inferred.</p>
    {findings === null ? <p>Dependency details are loading or unavailable.</p> : applicable.length === 0 ? <p>No authorized cable/JB dependency Finding is present. No path is inferred.</p> : <ul className="cross-discipline-outcome-list">
      {applicable.map((finding) => <li key={finding.finding_id}><code className="cross-discipline-machine-id">{finding.subcode}</code> · {finding.severity} dependency Finding</li>)}
    </ul>}
  </section>;
}
