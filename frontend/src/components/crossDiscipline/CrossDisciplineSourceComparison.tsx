import type { XDIFinding } from "../../api/types";

const SOURCE_RULES = new Set([
  "ei.instrument_power_required",
  "ei.motor_instrument_voltage",
]);

export function CrossDisciplineSourceComparison({ findings }: { findings: XDIFinding[] | null }) {
  const applicable = findings?.filter((finding) => SOURCE_RULES.has(finding.subcode)) ?? [];
  return <section className="cross-discipline-card cross-discipline-ei-card" aria-label="Electrical and instrumentation source comparison">
    <h3>Electrical ↔ Instrumentation comparison</h3>
    <p className="cross-discipline-advisory">Advisory derived result. Authorized operands remain in retained provenance.</p>
    {findings === null ? <p>Comparison details are loading or unavailable.</p> : applicable.length === 0 ? <p>No authorized comparison Finding is present. This does not imply a PASS.</p> : <ul className="cross-discipline-outcome-list">
      {applicable.map((finding) => <li key={finding.finding_id}><code className="cross-discipline-machine-id">{finding.subcode}</code> · {finding.severity} Finding</li>)}
    </ul>}
  </section>;
}
