import { useEffect, useMemo, useState } from "react";
import { Bot, BriefcaseBusiness, ChevronDown, ChevronLeft, ChevronRight, EyeOff, FileCheck2, FolderKanban, GripVertical, RotateCcw, Settings2 } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { ApiResult, Paginated, Project } from "../api/types";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../components/States";
import { PageHeader, Surface } from "../components/Page";
import { defaultLayout, loadLayout, saveLayout, type DashboardLayout, type WidgetId, type WidgetSize } from "../dashboard/layout";

const meta: Record<WidgetId, { title: string; kicker: string; icon: typeof FolderKanban }> = {
  projects: { title: "Active Projects", kicker: "Authorized portfolio", icon: FolderKanban },
  "engineering-work": { title: "Engineering Work", kicker: "Current workload", icon: BriefcaseBusiness },
  reports: { title: "Technical Reports", kicker: "Human review", icon: FileCheck2 },
  memory: { title: "Organizational Memory", kicker: "Approved knowledge", icon: ChevronDown },
  assistant: { title: "AI Capture Assistant", kicker: "Advisory only", icon: Bot },
};

function WidgetBody({ id, projects }: { id: WidgetId; projects: ApiResult<Paginated<Project>> | null }) {
  if (id === "projects") {
    if (!projects) return <LoadingState />; if (projects.state === "unavailable" || projects.state === "error") return <ErrorState unavailable={projects.state === "unavailable"} />;
    if (projects.state !== "success") return <EmptyState title="Projects unavailable" detail="No project information is disclosed for this context." />;
    if (!projects.data.items.length) return <EmptyState title="No visible projects" detail="Authorized projects will appear here." />;
    return <div className="project-list">{projects.data.items.slice(0, 4).map((p) => <Link to={`/projects/${p.id}`} className="project-row" key={p.id}><div><strong>{p.name}</strong><span>{p.project_code} · {p.customer.name}</span></div><div className="project-progress"><span>{p.progress}%</span><i><b style={{ width: `${p.progress}%` }} /></i></div><StatusBadge value={p.status} /></Link>)}</div>;
  }
  const content = {
    "engineering-work": ["Open the Engineering Workspace to review current captures and discipline context.", "/journal", "Open workspace"],
    reports: ["Review bounded Technical Report lists within an authorized Workspace.", "/reports", "View reports"],
    memory: ["Retrieve active, Human-admitted organizational knowledge without bypassing source access.", "/memory", "Open memory"],
    assistant: ["Prepare one uncertainty-aware refinement from an authorized Capture. AI output remains advisory.", "/assistant", "Request advice"],
  }[id] as string[];
  return <div className="widget-callout"><p>{content[0]}</p><Link className="text-link" to={content[1]}>{content[2]}<ChevronRight size={16} /></Link></div>;
}

export function DashboardPage() {
  const [layout, setLayout] = useState<DashboardLayout>(() => loadLayout()); const [customize, setCustomize] = useState(false); const [projects, setProjects] = useState<ApiResult<Paginated<Project>> | null>(null); const [dragged, setDragged] = useState<WidgetId | null>(null);
  useEffect(() => { void api.projects().then(setProjects); }, []);
  const visible = useMemo(() => layout.widgets.filter((w) => !w.hidden), [layout]);
  function update(next: DashboardLayout) { setLayout(next); saveLayout(next); }
  function move(id: WidgetId, delta: number) { const widgets = [...layout.widgets]; const from = widgets.findIndex((w) => w.id === id); const to = Math.max(0, Math.min(widgets.length - 1, from + delta)); widgets.splice(to, 0, widgets.splice(from, 1)[0]); update({ version: 1, widgets }); }
  function patch(id: WidgetId, values: Partial<{ size: WidgetSize; hidden: boolean }>) { update({ version: 1, widgets: layout.widgets.map((w) => w.id === id ? { ...w, ...values } : w) }); }
  function drop(id: WidgetId) { if (!dragged || dragged === id) return; const widgets = [...layout.widgets]; const from = widgets.findIndex((w) => w.id === dragged); const to = widgets.findIndex((w) => w.id === id); widgets.splice(to, 0, widgets.splice(from, 1)[0]); update({ version: 1, widgets }); setDragged(null); }
  return <div className="page"><PageHeader eyebrow="Engineering command center" title="Good work starts with context." description="Your authorized operational view across projects, engineering knowledge, and Human-controlled AI." action={<button className={`button ${customize ? "primary" : "secondary"}`} onClick={() => setCustomize(!customize)}><Settings2 size={17} />{customize ? "Finish customizing" : "Customize Dashboard"}</button>} />
    {customize && <Surface className="customize-bar"><div><strong>Customize your command center</strong><span>Reorder, resize, or hide presentation widgets. Engineering data and authority are never changed.</span></div><button className="button ghost" onClick={() => { localStorage.removeItem("satco.dashboard.layout.v1"); setLayout(structuredClone(defaultLayout)); }}><RotateCcw size={16} />Reset SATCO default</button></Surface>}
    <div className="dashboard-grid">{visible.map((widget) => { const Icon = meta[widget.id].icon; return <section className={`dashboard-widget size-${widget.size}`} key={widget.id} draggable={customize} onDragStart={() => setDragged(widget.id)} onDragOver={(e) => customize && e.preventDefault()} onDrop={() => drop(widget.id)}><header><div className="widget-title"><span className="widget-icon"><Icon size={19} /></span><div><span>{meta[widget.id].kicker}</span><h2>{meta[widget.id].title}</h2></div></div>{customize && <div className="widget-tools"><GripVertical aria-hidden="true" /><button onClick={() => move(widget.id, -1)} aria-label={`Move ${meta[widget.id].title} earlier`}><ChevronLeft /></button><button onClick={() => move(widget.id, 1)} aria-label={`Move ${meta[widget.id].title} later`}><ChevronRight /></button><select value={widget.size} onChange={(e) => patch(widget.id, { size: e.target.value as WidgetSize })} aria-label={`Size of ${meta[widget.id].title}`}><option value="compact">Compact</option><option value="standard">Standard</option><option value="wide">Wide</option></select><button onClick={() => patch(widget.id, { hidden: true })} aria-label={`Hide ${meta[widget.id].title}`}><EyeOff /></button></div>}</header><WidgetBody id={widget.id} projects={projects} /></section>; })}</div>
    {customize && layout.widgets.some((w) => w.hidden) && <Surface title="Hidden widgets" subtitle="Restore any widget to the dashboard."><div className="restore-list">{layout.widgets.filter((w) => w.hidden).map((w) => <button key={w.id} className="button secondary" onClick={() => patch(w.id, { hidden: false })}>{meta[w.id].title}</button>)}</div></Surface>}
  </div>;
}
