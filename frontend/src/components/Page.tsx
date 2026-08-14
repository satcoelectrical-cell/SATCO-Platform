import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description: string; action?: ReactNode }) {
  return <header className="page-header"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1><p>{description}</p></div>{action}</header>;
}
export function Surface({ children, className = "", title, subtitle }: { children: ReactNode; className?: string; title?: string; subtitle?: string }) {
  return <section className={`surface ${className}`}>{title && <header className="surface-header"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div></header>}{children}</section>;
}
