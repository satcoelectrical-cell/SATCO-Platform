import type { XDIFinding } from "../../api/types";

export function CrossDisciplineDependencyView({ findings }: { findings: XDIFinding[] | null }) {
  const applicable = findings?.filter((finding) => finding.subcode === "ei.cable_jb_path" || finding.subcode === "ic.valve_command_feedback" || finding.subcode === "ec.cabinet_power_path") ?? [];
  return <section className="cross-discipline-card cross-discipline-ei-card cross-discipline-ic-card" aria-label="Cross-discipline dependency">
    <h3>Declared dependency</h3>
    <p className="cross-discipline-advisory">Only a persisted authorized path gap is displayed; topology is never inferred.</p>
    {findings === null ? <p>Dependency details are loading or unavailable.</p> : applicable.length === 0 ? <p>No authorized dependency Finding is present. No path is inferred.</p> : <ul className="cross-discipline-outcome-list">
      {applicable.map((finding) => <li key={finding.finding_id}><code className="cross-discipline-machine-id">{finding.subcode}</code> · {finding.severity} dependency Finding</li>)}
    </ul>}
  </section>;
}
