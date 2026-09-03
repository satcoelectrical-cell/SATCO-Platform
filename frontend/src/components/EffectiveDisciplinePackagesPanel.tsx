import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ApiResult, EffectiveDisciplinePackages } from "../api/types";

export function EffectiveDisciplinePackagesPanel({projectId}:{projectId:number}) {
  const [result,setResult]=useState<ApiResult<EffectiveDisciplinePackages>|null>(null);
  useEffect(()=>{if (typeof api.effectiveDisciplinePackages === "function") void api.effectiveDisciplinePackages(projectId).then(setResult)},[projectId]);
  if(result?.state!=="success") return <section className="surface package-panel"><h2>Discipline availability</h2><p className="form-hint">Availability is unavailable or not disclosed.</p></section>;
  return <section className="surface package-panel"><h2>Discipline availability</h2><div className="package-list">{result.data.items.map(item=><div key={item.discipline_id}><strong>{item.display_name}</strong><span>{item.availability.replaceAll("_"," ")}</span></div>)}</div></section>;
}
