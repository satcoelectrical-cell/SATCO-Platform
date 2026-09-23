import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Bot, BriefcaseBusiness, ChevronLeft, ChevronRight, Clock3, EyeOff, FileCheck2, FolderKanban, GripVertical, Lightbulb, MemoryStick, RefreshCw, RotateCcw, Settings2, ShieldCheck, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import type { ApiResult } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "../components/States";
import { PageHeader, Surface } from "../components/Page";
import { commandMetrics, loadCommandCenter, orderedProjectWork, type CommandCenterData } from "../dashboard/commandCenter";
import { projectOptions, workspaceOptions } from "../productExperience/context";
import { resolveOwnerRoute, type OwnerRouteDescriptor } from "../productExperience/routes";
import { defaultLayout, loadLayout, saveLayout, type DashboardLayout, type WidgetId, type WidgetSize } from "../dashboard/layout";

const meta: Record<WidgetId, { title: string; kicker: string; icon: typeof FolderKanban }> = {
  projects: { title: "Active Projects", kicker: "Authorized portfolio", icon: FolderKanban },
  "engineering-work": { title: "Today’s Engineering Work", kicker: "Priority command queue", icon: BriefcaseBusiness },
  reports: { title: "Technical Reports", kicker: "Human-governed records", icon: FileCheck2 },
  memory: { title: "Organizational Memory", kicker: "Approved knowledge", icon: MemoryStick },
  assistant: { title: "AI Intelligence", kicker: "Human-controlled advisory", icon: Bot },
};

const formatDate = (value: string) => { const date = new Date(value); return Number.isFinite(date.getTime()) ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date) : "—"; };

function SourceEmpty({ state, title, detail }: { state: string; title: string; detail: string }) {
  if (state === "protected") return <ProtectedState />;
  if (state === "unavailable" || state === "error") return <ErrorState unavailable={state === "unavailable"} />;
  return <EmptyState title={title} detail={detail} />;
}

function ProjectsWidget({ data }: { data: CommandCenterData }) {
  const active = data.projects.filter((project) => ["active", "in_progress"].includes(project.status.toLowerCase()));
  if (!active.length) return <EmptyState title="No visible active projects" detail="Authorized active projects will appear here." />;
  return <div className="command-table-wrap"><table className="command-table"><caption className="sr-only">Authorized active project view</caption><thead><tr><th>Project</th><th>Customer</th><th>Priority</th><th>Status</th><th>Progress</th><th>Updated</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>{active.slice(0, 6).map((project) => <tr key={project.id}><td><Link to={`/projects/${project.id}`}><strong>{project.name}</strong><span>{project.project_code}</span></Link></td><td>{project.customer.name}</td><td><StatusBadge value={project.priority} /></td><td><StatusBadge value={project.status} /></td><td><div className="table-progress"><span>{project.progress}%</span><i><b style={{ width: `${Math.max(0, Math.min(100, project.progress))}%` }} /></i></div></td><td>{formatDate(project.updated_at)}</td><td><Link className="row-open" aria-label={`Open ${project.name}`} to={`/projects/${project.id}`}><ArrowUpRight size={16} /></Link></td></tr>)}</tbody></table></div>;
}

function EngineeringWorkWidget({ data }: { data: CommandCenterData }) {
  const work = orderedProjectWork(data.projects);
  if (!work.length && !data.captures.length) return <EmptyState title="No visible engineering work" detail="Authorized priority and Capture context will appear here." />;
  const recent = [...data.projects].sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at)).slice(0, 4);
  return <div className="work-columns"><div className="work-queue"><div className="subpanel-title"><Lightbulb size={16} /><span>Priority queue</span></div>{work.slice(0, 4).map((project, index) => <Link to={`/projects/${project.id}`} className="work-item" key={project.id}><span className="work-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{project.name}</strong><span>{project.project_code} · {project.priority} priority</span></div><StatusBadge value={project.status} /><ChevronRight size={16} /></Link>)}</div><div className="activity-feed"><div className="subpanel-title"><Clock3 size={16} /><span>Authorized project updates</span></div>{recent.map((project) => <Link to={`/projects/${project.id}`} className="activity-item" key={project.id}><i /><div><strong>{project.name}</strong><span>Project record updated · {formatDate(project.updated_at)}</span></div></Link>)}{data.captures.length > 0 && <Link to="/journal" className="activity-item capture"><i /><div><strong>{data.captures.length} visible Capture context{data.captures.length === 1 ? "" : "s"}</strong><span>Continue Human-led engineering work</span></div></Link>}</div></div>;
}

function ReportsWidget({ data, openOwner }: { data: CommandCenterData;openOwner:(route:OwnerRouteDescriptor)=>void }) {
  if (!data.reports.length) return <SourceEmpty state={data.sourceStates.reports} title="No visible reports" detail="Scoped Technical Reports will appear here." />;
  return <div className="intel-list">{data.reports.map((report) => <button type="button" onClick={()=>openOwner({routeKind:"technical_report",label:report.purpose,projectId:data.selectedProjectId!,workspaceId:report.workspace_id,targetHandle:report.id,sourceVersion:report.version})} className="intel-row" key={report.id}><span className="intel-icon"><FileCheck2 size={16} /></span><div><strong>{report.purpose}</strong><span>v{report.version} · {report.lifecycle} · {formatDate(report.updated_at)}</span></div><ChevronRight size={16} /></button>)}<Link to="/reports" className="panel-link">Open Technical Reports <ArrowUpRight size={15} /></Link></div>;
}

function MemoryWidget({ data, openOwner }: { data: CommandCenterData;openOwner:(route:OwnerRouteDescriptor)=>void }) {
  if (!data.memory.length) return <SourceEmpty state={data.sourceStates.memory} title="No visible active memory" detail="Authorized Human-admitted knowledge will appear here." />;
  return <div className="intel-list">{data.memory.map((memory) => <button type="button" onClick={()=>openOwner({routeKind:"organizational_memory",label:memory.purpose,projectId:data.selectedProjectId!,workspaceId:memory.workspace_id,targetHandle:memory.memory_id,sourceVersion:memory.version})} className="intel-row" key={memory.memory_id}><span className="intel-icon memory"><ShieldCheck size={16} /></span><div><strong>{memory.purpose}</strong><span>Active · admitted {formatDate(memory.admitted_at)}</span></div><ChevronRight size={16} /></button>)}<Link to="/memory" className="panel-link">Open Organizational Memory <ArrowUpRight size={15} /></Link></div>;
}

function AssistantWidget({ data }: { data: CommandCenterData }) {
  const latest = [...data.captures].sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at))[0];
  return <div className="ai-command-panel"><div className="ai-orbit"><Sparkles /><span>AI</span></div><div className="ai-command-copy"><span className="ai-advisory"><ShieldCheck size={14} />Advisory · never authoritative</span><h3>{latest ? "Capture context is ready for Human-requested analysis." : "No visible Capture context is ready."}</h3><p>{latest ? `Capture ${latest.id.slice(0, 8)}… · ${latest.source_kind} · v${latest.version}. SATCO can prepare uncertainty-aware advice only when you explicitly request it.` : "Open Engineering Workspace to establish authorized Capture context. No AI suggestion or count is manufactured here."}</p>{latest && <div className="ai-context"><span>Discipline<strong>{latest.discipline ?? "Not specified"}</strong></span><span>Lifecycle<strong>{latest.lifecycle}</strong></span><span>Updated<strong>{formatDate(latest.updated_at)}</strong></span></div>}<Link className="button primary" to="/assistant"><Bot size={16} />Open AI Capture Assistant</Link></div></div>;
}

function WidgetBody({ id, data, openOwner }: { id: WidgetId; data: CommandCenterData;openOwner:(route:OwnerRouteDescriptor)=>void }) {
  if (id === "projects") return <ProjectsWidget data={data} />;
  if (id === "engineering-work") return <EngineeringWorkWidget data={data} />;
  if (id === "reports") return <ReportsWidget data={data} openOwner={openOwner} />;
  if (id === "memory") return <MemoryWidget data={data} openOwner={openOwner} />;
  return <AssistantWidget data={data} />;
}

export function DashboardPage() {
  const [layout, setLayout] = useState<DashboardLayout>(() => loadLayout());
  const [customize, setCustomize] = useState(false);
  const [result, setResult] = useState<ApiResult<CommandCenterData> | null>(null);
  const [dragged, setDragged] = useState<WidgetId | null>(null);
  const [projectId,setProjectId]=useState<number|null>(null);
  const [workspaceId,setWorkspaceId]=useState<number|null>(null);
  const navigate=useNavigate();
  const [routeMessage,setRouteMessage]=useState("");
  async function openOwner(route:OwnerRouteDescriptor){setRouteMessage("");const path=await resolveOwnerRoute(route);if(path)navigate(path);else setRouteMessage("That owner target is no longer available in the authorized context.");}
  const load = useCallback(() => { setResult(null); void loadCommandCenter({projectId,workspaceId}).then(setResult); }, [projectId,workspaceId]);
  useEffect(load, [load]);
  const visible = useMemo(() => layout.widgets.filter((w) => !w.hidden), [layout]);
  const isDefaultComposition = layout.widgets.every((widget, index) => {
    const baseline = defaultLayout.widgets[index];
    return widget.id === baseline.id && widget.size === baseline.size && widget.hidden === baseline.hidden;
  });
  function update(next: DashboardLayout) { setLayout(next); saveLayout(next); }
  function move(id: WidgetId, delta: number) { const widgets = [...layout.widgets]; const from = widgets.findIndex((w) => w.id === id); const to = Math.max(0, Math.min(widgets.length - 1, from + delta)); widgets.splice(to, 0, widgets.splice(from, 1)[0]); update({ version: 1, widgets }); }
  function patch(id: WidgetId, values: Partial<{ size: WidgetSize; hidden: boolean }>) { update({ version: 1, widgets: layout.widgets.map((w) => w.id === id ? { ...w, ...values } : w) }); }
  function drop(id: WidgetId) { if (!dragged || dragged === id) return; const widgets = [...layout.widgets]; const from = widgets.findIndex((w) => w.id === dragged); const to = widgets.findIndex((w) => w.id === id); widgets.splice(to, 0, widgets.splice(from, 1)[0]); update({ version: 1, widgets }); setDragged(null); }

  const projectChoices=result?.state==="success"?projectOptions(result.data.projects):[];
  const workspaceChoices=result?.state==="success"?workspaceOptions(result.data.workspaces,projectId):[];
  return <div className="page command-page"><PageHeader eyebrow="Engineering command center" title="Your engineering priorities, in context." description="A bounded authorized view of visible work, project movement, governed knowledge, and Human-controlled AI." action={<div className="header-actions"><button className="button ghost" onClick={load}><RefreshCw size={16} />Refresh view</button><button className={`button ${customize ? "primary" : "secondary"}`} onClick={() => setCustomize(!customize)}><Settings2 size={17} />{customize ? "Finish customizing" : "Customize Dashboard"}</button></div>} />
    <Surface title="Engineering context" subtitle="Choose authorized context explicitly; SATCO never treats the first visible record as authority."><div className="bootstrap-form"><label>Project<select aria-label="Command Center Project" value={projectId??""} onChange={(e)=>{const value=e.target.value?Number(e.target.value):null;setProjectId(value);setWorkspaceId(null);}}><option value="">Select Project</option>{projectChoices.map(option=><option key={option.value} value={option.value}>{option.label}</option>)}</select></label><label>Engineering Workspace<select aria-label="Command Center Workspace" value={workspaceId??""} disabled={projectId==null} onChange={(e)=>setWorkspaceId(e.target.value?Number(e.target.value):null)}><option value="">Select Workspace</option>{workspaceChoices.map(option=><option key={option.value} value={option.value}>{option.label}</option>)}</select></label></div></Surface>
    {!result && <LoadingState label="Composing your authorized Command Center…" />}
    {result?.state === "protected" && <ProtectedState />}
    {result && ["unavailable", "error", "invalid"].includes(result.state) && <ErrorState retry={load} unavailable={result.state === "unavailable"} />}
    {result?.state === "success" && <>
<Surface title="Engineering intelligence" subtitle="Independent authorized owner slices; advisory outputs never become engineering authority."><div className="kpi-strip" aria-label="Engineering intelligence slices">{Object.entries(result.data.intelligence).map(([key,slice])=><article className="kpi-card tone-neutral" key={key}><span>{key.replaceAll("_"," ")}</span><strong>{slice.state}</strong><small>{slice.visibleCount===undefined?"No count exposed":slice.visibleCount+" visible record"+(slice.visibleCount===1?"":"s")}</small>{projectId!=null&&["standards","evidence","retention","performance"].includes(key)?<button type="button" className="button ghost compact" onClick={()=>void openOwner({routeKind:({standards:"standards",evidence:"evidence_workbench",retention:"retention",performance:"engineering_performance_source"} as const)[key as "standards"|"evidence"|"retention"|"performance"],label:key.replaceAll("_"," "),projectId,workspaceId})}>Open owner</button>:null}</article>)}</div>{routeMessage?<p role="status">{routeMessage}</p>:null}</Surface>
            <section className="kpi-strip" aria-label="Visible engineering summary">{commandMetrics(result.data).map((metric) => <article className={`kpi-card tone-${metric.tone}`} key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.detail}</small></article>)}</section>
      {customize && <Surface className="customize-bar"><div><strong>Customize your Command Center</strong><span>Reorder, resize, or hide presentation widgets. Engineering data and authority never change.</span></div><button className="button ghost" onClick={() => { localStorage.removeItem("satco.dashboard.layout.v1"); setLayout(structuredClone(defaultLayout)); }}><RotateCcw size={16} />Reset SATCO default</button></Surface>}
      <div className="dashboard-grid command-grid" data-default-composition={isDefaultComposition}>{visible.map((widget) => { const Icon = meta[widget.id].icon; return <section className={`dashboard-widget command-widget widget-${widget.id} size-${widget.size}`} data-widget-id={widget.id} key={widget.id} draggable={customize} onDragStart={() => setDragged(widget.id)} onDragOver={(e) => customize && e.preventDefault()} onDrop={() => drop(widget.id)}><header><div className="widget-title"><span className="widget-icon"><Icon size={19} /></span><div><span>{meta[widget.id].kicker}</span><h2>{meta[widget.id].title}</h2></div></div>{customize && <div className="widget-tools"><GripVertical aria-hidden="true" /><button onClick={() => move(widget.id, -1)} aria-label={`Move ${meta[widget.id].title} earlier`}><ChevronLeft /></button><button onClick={() => move(widget.id, 1)} aria-label={`Move ${meta[widget.id].title} later`}><ChevronRight /></button><select value={widget.size} onChange={(e) => patch(widget.id, { size: e.target.value as WidgetSize })} aria-label={`Size of ${meta[widget.id].title}`}><option value="compact">Compact</option><option value="standard">Standard</option><option value="wide">Wide</option></select><button onClick={() => patch(widget.id, { hidden: true })} aria-label={`Hide ${meta[widget.id].title}`}><EyeOff /></button></div>}</header><WidgetBody id={widget.id} data={result.data} openOwner={(route)=>void openOwner(route)} /></section>; })}</div>
      {customize && layout.widgets.some((w) => w.hidden) && <Surface title="Hidden widgets" subtitle="Restore any widget to the Command Center."><div className="restore-list">{layout.widgets.filter((w) => w.hidden).map((w) => <button key={w.id} className="button secondary" onClick={() => patch(w.id, { hidden: false })}>{meta[w.id].title}</button>)}</div></Surface>}
    </>}
  </div>;
}
