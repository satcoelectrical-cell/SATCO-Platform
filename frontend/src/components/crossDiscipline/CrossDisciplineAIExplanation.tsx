import type { XDIAIExplanation } from "../../api/types";

export function CrossDisciplineAIExplanation({ explanation }: { explanation: XDIAIExplanation | null }) {
  if (!explanation?.summary) return null;
  return <section className="cross-discipline-ai-explanation" aria-live="polite">
    <h3>Optional AI explanation</h3>
    <p className="cross-discipline-advisory">Non-authoritative draft guidance only.</p>
    <p>{explanation.summary}</p>
  </section>;
}
