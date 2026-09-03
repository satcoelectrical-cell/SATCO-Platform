import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ApiResult, OrganizationPackageConfiguration, SupportedPackages } from "../api/types";

export function OrganizationPackageConfigurationPanel() {
  const [configuration,setConfiguration]=useState<ApiResult<OrganizationPackageConfiguration>|null>(null);
  const [supported,setSupported]=useState<ApiResult<SupportedPackages>|null>(null);
  const [rationale,setRationale]=useState(""); const [busy,setBusy]=useState(false);
  const load=()=>{if(typeof api.organizationPackageConfiguration==="function") void api.organizationPackageConfiguration().then(setConfiguration);if(typeof api.supportedPackages==="function") void api.supportedPackages().then(setSupported)};
  useEffect(load,[]);
  if(configuration?.state!=="success"||supported?.state!=="success"||!Array.isArray(configuration.data.enabled_selections)||!Array.isArray(supported.data.items)) return <section className="surface"><h2>Package configuration</h2><p className="form-hint">Package configuration is unavailable or not disclosed.</p></section>;
  const enabled=new Set(configuration.data.enabled_selections.map(item=>`${item.package_key}@${item.package_version}`));
  const toggle=(key:string)=>{ if(enabled.has(key)) enabled.delete(key); else enabled.add(key); setConfiguration({state:"success",data:{...configuration.data,enabled_selections:supported.data.items.filter(item=>enabled.has(`${item.package_key}@${item.package_version}`)).map(item=>({package_key:item.package_key,package_version:item.package_version}))}}); };
  const save=async()=>{setBusy(true);const result=await api.replaceOrganizationPackageConfiguration({expected_configuration_version:configuration.data.configuration_version,enabled_selections:configuration.data.enabled_selections,rationale});if(result.state==="success"){setRationale("");load()}setBusy(false)};
  return <section className="surface package-panel"><h2>Discipline package configuration</h2><p>Configuration is not commercial entitlement and never grants engineering authority.</p><div className="package-list">{supported.data.items.map(item=>{const key=`${item.package_key}@${item.package_version}`;return <label key={key}><input type="checkbox" checked={enabled.has(key)} onChange={()=>toggle(key)} />{item.package_key} <small>{item.package_version}</small></label>})}</div><label>Rationale<textarea value={rationale} onChange={e=>setRationale(e.target.value)} maxLength={2000} /></label><button className="button secondary" disabled={busy||!rationale.trim()} onClick={()=>void save()}>Save package configuration</button></section>;
}
