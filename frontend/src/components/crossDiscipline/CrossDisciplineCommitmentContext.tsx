import type { XDIFinding } from "../../api/types";

export function CrossDisciplineCommitmentContext({ findings }: { findings: XDIFinding[] | null }) {
  const applicable = findings?.filter((finding) => finding.subcode === "ei.handoff_complete" || finding.subcode === "ic.commitment_fulfilment" || finding.subcode === "ec.commitment_dispute") ?? [];
  return <section className="cross-discipline-card cross-discipline-ei-card cross-discipline-ic-card" aria-label="Cross-discipline commitment context">
    <h3>Commitment context</h3>
    <p className="cross-discipline-advisory">Current-use commitment and declaration presence only.</p>
    {findings === null ? <p>Commitment details are loading or unavailable.</p> : applicable.length === 0 ? <p>No authorized commitment Finding is present. This does not establish fulfilment.</p> : <ul className="cross-discipline-outcome-list">
      {applicable.map((finding) => <li key={finding.finding_id}><code className="cross-discipline-machine-id">{finding.subcode}</code> · {finding.current_state}</li>)}
    </ul>}
  </section>;
}
