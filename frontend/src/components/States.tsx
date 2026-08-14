import { AlertTriangle, Inbox, LoaderCircle, RefreshCw, ShieldAlert } from "lucide-react";

export function LoadingState({ label = "Loading authorized engineering data…" }: { label?: string }) {
  return <div className="state-box" role="status"><LoaderCircle className="spin" aria-hidden="true" /><strong>{label}</strong></div>;
}
export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="state-box"><Inbox aria-hidden="true" /><strong>{title}</strong><span>{detail}</span></div>;
}
export function ProtectedState() {
  return <div className="state-box" role="status"><ShieldAlert aria-hidden="true" /><strong>Not available</strong><span>This item is unavailable or outside your current authorized context.</span></div>;
}
export function ErrorState({ retry, unavailable = false }: { retry?: () => void; unavailable?: boolean }) {
  return <div className="state-box" role="alert"><AlertTriangle aria-hidden="true" /><strong>{unavailable ? "Service temporarily unavailable" : "We couldn’t load this view"}</strong><span>No protected details were disclosed.</span>{retry && <button className="button secondary" onClick={retry}><RefreshCw size={16} />Retry</button>}</div>;
}
export function StatusBadge({ value }: { value: string }) { return <span className={`badge badge-${value.toLowerCase().replaceAll("_", "-")}`}>{value.replaceAll("_", " ")}</span>; }
