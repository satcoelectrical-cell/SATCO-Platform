import type { XDIPotentialImpact } from "../../api/types";

export function CrossDisciplinePotentialImpactView({ impact }: { impact: XDIPotentialImpact | null }) {
  if (!impact) return null;
  return <section className="cross-discipline-potential-impact" aria-live="polite">
    <h3>Potential Change Impact</h3>
    <p className="cross-discipline-advisory">Advisory only. Project Control remains the canonical owner.</p>
    <p>{impact.state === "reconciled" ? "Potential Impact reconciled." : "Impact handoff is pending; no success is implied."}</p>
  </section>;
}
