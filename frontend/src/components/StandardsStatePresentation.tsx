export function StandardsStatePresentation({ state }: { state:string }) {
  const normalized = state.replaceAll("_", " ");
  const safeClass = state.toLowerCase().replace(/[^a-z0-9_-]/g, "-");
  return <span className={`standards-state standards-state-${safeClass}`} aria-label={`Status: ${normalized}`}><span aria-hidden="true">●</span>{normalized}</span>;
}
