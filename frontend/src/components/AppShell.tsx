import { useEffect, useRef, useState } from "react";
import { Bot, BookOpenText, BriefcaseBusiness, ChevronRight, FolderKanban, LayoutDashboard, LockKeyhole, LogOut, Menu, PanelLeftClose, Settings, ShieldCheck, X } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const navigation = [
  ["/", "Dashboard", LayoutDashboard], ["/projects", "Projects", FolderKanban],
  ["/standards", "Standards", BookOpenText],
  ["/journal", "Engineering Workspace", BriefcaseBusiness], ["/reports", "Technical Reports", BookOpenText],
  ["/memory", "Organizational Memory", PanelLeftClose], ["/assistant", "AI Capture Assistant", Bot],
] as const;

export function AppShell() {
  const [open, setOpen] = useState(false); const auth = useAuth(); const location = useLocation();
  const sidebarRef = useRef<HTMLElement>(null); const menuButtonRef = useRef<HTMLButtonElement>(null); const closeButtonRef = useRef<HTMLButtonElement>(null); const mainRef = useRef<HTMLElement>(null); const previousPath = useRef(location.pathname);
  const current = navigation.find(([path]) => path === "/" ? location.pathname === "/" : location.pathname.startsWith(path));
  const closeNavigation = (restoreFocus = true) => { setOpen(false); if (restoreFocus) window.setTimeout(() => menuButtonRef.current?.focus(), 0); };
  useEffect(() => {
    if (!open) return;
    closeButtonRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); closeNavigation(); return; }
      if (event.key !== "Tab" || !sidebarRef.current) return;
      const focusable = Array.from(sidebarRef.current.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])')).filter((element) => !element.hasAttribute("hidden"));
      if (!focusable.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open]);
  useEffect(() => {
    if (previousPath.current !== location.pathname) {
      previousPath.current = location.pathname; setOpen(false); mainRef.current?.focus();
    }
  }, [location.pathname]);
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside ref={sidebarRef} id="application-navigation" className={`sidebar ${open ? "open" : ""}`} aria-label="Application sidebar">
      <div className="brand"><div className="brand-mark" aria-hidden="true">S</div><div><strong>SATCO</strong><span>Engineering Command Center</span></div><button ref={closeButtonRef} className="icon-button close-nav" onClick={() => closeNavigation()} aria-label="Close navigation"><X aria-hidden="true" /></button></div>
      <nav aria-label="Primary navigation">{navigation.map(([to, label, Icon]) => <NavLink key={to} to={to} end={to === "/"} onClick={() => setOpen(false)}><Icon size={19} aria-hidden="true" /><span>{label}</span><ChevronRight className="nav-arrow" size={16} aria-hidden="true" /></NavLink>)}<NavLink to="/account" onClick={() => setOpen(false)}><Settings size={19} aria-hidden="true" /><span>My account</span><ChevronRight className="nav-arrow" size={16} aria-hidden="true" /></NavLink>{auth.profile?.role === "admin" ? <NavLink to="/organization-admin" onClick={() => setOpen(false)}><ShieldCheck size={19} aria-hidden="true" /><span>Organization Admin</span><ChevronRight className="nav-arrow" size={16} aria-hidden="true" /></NavLink> : null}</nav>
      <div className="sidebar-footer"><span className="environment-dot" aria-hidden="true" />Protected engineering environment<button className="signout" onClick={auth.logout}><LogOut size={17} aria-hidden="true" />Sign out</button></div>
    </aside>
    {open && <button className="nav-scrim" tabIndex={-1} aria-label="Close navigation" onClick={() => closeNavigation()} />}
    <div className="app-column"><header className="topbar"><button ref={menuButtonRef} className="icon-button menu-button" onClick={() => setOpen(true)} aria-label="Open navigation" aria-expanded={open} aria-controls="application-navigation"><Menu aria-hidden="true" /></button><div className="context"><span>{auth.profile?.organization.name ?? "SATCO"} / Engineering Command Center</span><strong>{current?.[1] ?? (location.pathname === "/organization-admin" ? "Organization Admin" : location.pathname === "/account" ? "My account" : "SATCO")}</strong></div><div className="topbar-rule" /><div className="trust-indicator"><LockKeyhole size={14} aria-hidden="true" />Authenticated · {auth.profile?.organization.name ?? "Organization context"} · server-derived</div></header><main ref={mainRef} id="main-content" tabIndex={-1} aria-label={`${current?.[1] ?? "SATCO"} content`}><Outlet /></main></div>
  </div>;
}
