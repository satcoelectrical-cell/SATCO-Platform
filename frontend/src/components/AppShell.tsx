import { useState } from "react";
import { Bot, BookOpenText, BriefcaseBusiness, ChevronRight, FolderKanban, LayoutDashboard, LockKeyhole, LogOut, Menu, PanelLeftClose, X } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const navigation = [
  ["/", "Dashboard", LayoutDashboard], ["/projects", "Projects", FolderKanban],
  ["/journal", "Engineering Workspace", BriefcaseBusiness], ["/reports", "Technical Reports", BookOpenText],
  ["/memory", "Organizational Memory", PanelLeftClose], ["/assistant", "AI Capture Assistant", Bot],
] as const;

export function AppShell() {
  const [open, setOpen] = useState(false); const auth = useAuth(); const location = useLocation();
  const current = navigation.find(([path]) => path === "/" ? location.pathname === "/" : location.pathname.startsWith(path));
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className={`sidebar ${open ? "open" : ""}`} aria-label="Application sidebar">
      <div className="brand"><div className="brand-mark">S</div><div><strong>SATCO</strong><span>Engineering Command Center</span></div><button className="icon-button close-nav" onClick={() => setOpen(false)} aria-label="Close navigation"><X /></button></div>
      <nav aria-label="Primary navigation">{navigation.map(([to, label, Icon]) => <NavLink key={to} to={to} end={to === "/"} onClick={() => setOpen(false)}><Icon size={19} /><span>{label}</span><ChevronRight className="nav-arrow" size={16} /></NavLink>)}</nav>
      <div className="sidebar-footer"><span className="environment-dot" />Protected engineering environment<button className="signout" onClick={auth.logout}><LogOut size={17} />Sign out</button></div>
    </aside>
    {open && <button className="nav-scrim" aria-label="Close navigation" onClick={() => setOpen(false)} />}
    <div className="app-column"><header className="topbar"><button className="icon-button menu-button" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu /></button><div className="context"><span>SATCO / Engineering Command Center</span><strong>{current?.[1] ?? "SATCO"}</strong></div><div className="topbar-rule" /><div className="trust-indicator"><LockKeyhole size={14} />Authenticated · Organization context · server-derived</div></header><main id="main-content"><Outlet /></main></div>
  </div>;
}
