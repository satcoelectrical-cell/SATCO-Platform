import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ApiResult, ProjectPackageConfiguration, SupportedPackages } from "../api/types";

export function ProjectPackageConfigurationPanel({projectId}:{projectId:number}) {
  const [result,setResult]=useState<ApiResult<ProjectPackageConfiguration>|null>(null);
  const [supported,setSupported]=useState<ApiResult<SupportedPackages>|null>(null);
  const [profileId,setProfileId]=useState(""); const [rationale,setRationale]=useState(""); const [selected,setSelected]=useState<string[]>([]); const [message,setMessage]=useState("");
  useEffect(()=>{if (typeof api.projectPackageConfiguration === "function") void api.projectPackageConfiguration(projectId).then(setResult)},[projectId]);
  useEffect(()=>{if (typeof api.supportedPackages === "function") void api.supportedPackages().then(setSupported)},[]);
  if(result?.state!=="success") return <section className="surface package-panel"><h2>Project package configuration</h2><p className="form-hint">Configuration is unavailable or not disclosed.</p></section>;
  const options=supported?.state==="success"?supported.data.items:[];
  const configuration=result.data;
  const toggle=(key:string)=>setSelected(current=>current.includes(key)?current.filter(value=>value!==key):[...current,key]);
  const save=async()=>{if(!profileId.trim()||!rationale.trim())return;const selections=options.filter(item=>selected.includes(`${item.package_key}@${item.package_version}`)).map(item=>({package_key:item.package_key,package_version:item.package_version}));const response=await api.replaceProjectPackageConfiguration(projectId,{expected_configuration_version:configuration.configuration_version,profile_id:profileId,selections,rationale});if(response.state==="success"){setResult(response);setMessage("Configuration saved.")}else setMessage("Configuration was not accepted.")};
  const remove=async()=>{if(!rationale.trim())return;const response=await api.removeProjectPackageConfiguration(projectId,{expected_configuration_version:configuration.configuration_version,rationale});if(response.state==="success"){setResult(response);setMessage("Configuration removed.")}else setMessage("Configuration could not be removed.")};
  return <section className="surface package-panel"><h2>Project package configuration</h2><p>{configuration.state==="NOT_CONFIGURED"?"This Project is not configured. Future-discipline Workspaces remain representable.":`Revision ${configuration.configuration_revision} · profile ${configuration.profile_id}`}</p>{configuration.state==="CONFIGURED"&&<ul>{configuration.selections.map(item=><li key={`${item.package_key}@${item.package_version}`}>{item.package_key} {item.package_version}</li>)}</ul>}<label>Compatibility profile<input value={profileId} onChange={e=>setProfileId(e.target.value)} maxLength={64}/></label><div className="package-list">{options.map(item=>{const key=`${item.package_key}@${item.package_version}`;return <label key={key}><input type="checkbox" checked={selected.includes(key)} onChange={()=>toggle(key)}/>{item.package_key} <small>{item.package_version}</small></label>})}</div><label>Rationale<textarea value={rationale} onChange={e=>setRationale(e.target.value)} maxLength={2000}/></label><div><button className="button secondary" onClick={()=>void save()}>Save exact configuration</button>{configuration.state==="CONFIGURED"&&<button className="button ghost" onClick={()=>void remove()}>Remove configuration</button>}</div>{message&&<p className="form-message" role="status">{message}</p>}</section>;
}
