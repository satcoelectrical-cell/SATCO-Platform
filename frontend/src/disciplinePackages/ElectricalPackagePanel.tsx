import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, PackageObjectCreateResult, PackageRuleResult } from "../api/types";
import { PackageWorkspaceShell, type PackagePanelProps } from "./PackageWorkspaceShell";

const OBJECTS = ["motor","transformer","mcc","switchgear","electrical_panel","electrical_cable","electrical_feeder","electrical_power_source"] as const;
const RELATIONSHIPS = ["powered_by","protected_by","isolated_by","earthed_through","connected_to_busbar","controlled_by_feeder","backed_up_by_ups"] as const;
const INPUTS = ["system_voltage_basis","load_duty_basis","source_feeder_basis","protection_basis","earthing_basis"] as const;
const DELIVERABLES = ["electrical_load_list","single_line_diagram","electrical_cable_schedule","electrical_equipment_datasheet"] as const;
const EVIDENCE = ["voltage_source_basis_evidence","load_basis_evidence","protection_feeder_basis_evidence","deliverable_review_evidence"] as const;
const RULES = ["object_relationship_integrity","required_input_completeness","source_feeder_connectivity","evidence_sufficiency","deliverable_readiness"] as const;

export function ElectricalPackagePanel({ state = "UNAVAILABLE", projectId, workspaceId }: Readonly<PackagePanelProps>) {
  const [objectType,setObjectType]=useState<(typeof OBJECTS)[number]>("motor");
  const [displayValue,setDisplayValue]=useState("");
  const [rationale,setRationale]=useState("");
  const [creation,setCreation]=useState<ApiResult<PackageObjectCreateResult>|null>(null);
  const [assessment,setAssessment]=useState<ApiResult<PackageRuleResult>|null>(null);
  async function createObject(event:FormEvent){event.preventDefault();if(!projectId||!workspaceId)return;setCreation(await api.createElectricalObject(projectId,workspaceId,{declaration_id:`electrical.object.${objectType}`,primary_identifier_display_value:displayValue,primary_identifier_evidence_references:[],steward_id:null,rationale}));}
  async function evaluate(){if(!projectId||!workspaceId)return;setAssessment(await api.evaluateElectricalRule(projectId,workspaceId,{hook_id:"electrical.required_input_completeness",hook_version:"1.0.0",envelope:{objects:[],relationships:[],deliverables:[],contexts:[],evidence:[],missing_required_ids:[],partial:true,protected:false,stale:false}}));}
  return <PackageWorkspaceShell title="Electrical V1" state={state}>
    <p>Server-authorized Electrical engineering package. Deterministic checks are advisory or gate only the requested package operation.</p>
    <div className="package-catalog-grid">
      <section><h3>Objects · 8</h3><ul>{OBJECTS.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul></section>
      <section><h3>Relationships · 7</h3><ul>{RELATIONSHIPS.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul></section>
      <section><h3>Inputs / Context · 5</h3><ul>{INPUTS.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul></section>
      <section><h3>Evidence & Deliverables</h3><p>{EVIDENCE.length} evidence requirements · {DELIVERABLES.length} deliverables</p><ul>{DELIVERABLES.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul></section>
      <section><h3>Deterministic Guidance · 5</h3><ul>{RULES.map(x=><li key={x}>{x.replaceAll("_"," ")}</li>)}</ul><button type="button" className="button secondary" onClick={evaluate}>Evaluate bounded readiness</button>{assessment?.state==="success"?<p role="status">{assessment.data.status}</p>:null}</section>
    </div>
    <form className="bootstrap-form" onSubmit={createObject}><h3>Create Object with required primary Identifier</h3><label>Object declaration<select value={objectType} onChange={e=>setObjectType(e.target.value as typeof objectType)}>{OBJECTS.map(x=><option key={x} value={x}>{x.replaceAll("_"," ")}</option>)}</select></label><label>Primary identifier<input required minLength={1} maxLength={128} value={displayValue} onChange={e=>setDisplayValue(e.target.value)}/></label><label>Rationale<textarea required minLength={1} maxLength={2000} value={rationale} onChange={e=>setRationale(e.target.value)}/></label><button className="button primary">Create atomic Object + Identifier</button>{creation?.state==="success"?<p role="status">Created {creation.data.primary_identifier.display_value}</p>:creation?<p role="alert">Operation {creation.state}</p>:null}</form>
  </PackageWorkspaceShell>;
}
