import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, StandardIdentityView, StandardsPage } from "../api/types";
import { StandardsStatePresentation } from "./StandardsStatePresentation";

export function StandardsRegistryPanel() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<ApiResult<StandardsPage> | null>(null);
  const [detail, setDetail] = useState<ApiResult<StandardIdentityView> | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);
  const statusRef = useRef<HTMLParagraphElement>(null);
  const detailRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (result && (result.state !== "success" || !result.data.items.length)) statusRef.current?.focus();
  }, [result]);
  useEffect(() => { if (detail) detailRef.current?.focus(); }, [detail]);

  async function search(event: FormEvent) {
    event.preventDefault(); setDetail(null); setDetailId(null); setResult(null);
    setResult(await api.standards(query.trim()));
  }
  async function openDetail(id: string) {
    setDetailId(id); setDetail(null); setDetail(await api.standard(id));
  }

  return <section className="standards-panel" aria-labelledby="standards-registry-title">
    <h2 id="standards-registry-title">Standards registry</h2>
    <p>Metadata search only. Selection, applicability, approval, and acceptance remain Human-governed.</p>
    <form onSubmit={search}><label>Search registry metadata<input value={query} onChange={(event) => setQuery(event.target.value)} maxLength={120} /></label><button className="button secondary">Search</button></form>
    <p ref={statusRef} role="status" tabIndex={-1}>{result?.state === "protected" ? "No standards metadata is available." : result?.state !== "success" && result ? "Registry is unavailable." : result?.state === "success" && !result.data.items.length ? "No matching standards metadata." : ""}</p>
    {result?.state === "success" ? <div className="standards-list">{result.data.items.map((item) => <article key={item.standard_id}>
      <div className="standards-row-heading"><strong><bdi dir="ltr">{item.issuer} · {item.designation}</bdi></strong><StandardsStatePresentation state={item.retired_from_new_selection ? "superseded" : "current"} /></div>
      <span>{item.title}</span><span>{item.catalog_scope === "organization_private" ? "Organization-private metadata" : "Trusted global metadata"}</span>
      <code dir="ltr">{item.standard_id}</code>
      <button type="button" className="button ghost compact" aria-expanded={detailId === item.standard_id && detail?.state === "success"} onClick={() => void openDetail(item.standard_id)}>Open metadata detail</button>
    </article>)}</div> : null}
    {detailId ? <div ref={detailRef} className="standards-detail" role="status" tabIndex={-1}>{!detail ? <p>Loading authorized metadata detail…</p> : detail.state === "protected" ? <p>This standards detail is not available.</p> : detail.state !== "success" ? <p>Standards detail could not be loaded.</p> : <article>
      <div className="standards-row-heading"><h3><bdi dir="ltr">{detail.data.issuer} · {detail.data.designation}</bdi></h3><StandardsStatePresentation state={detail.data.retired_from_new_selection ? "superseded" : "current"} /></div>
      <p>{detail.data.title}</p><p>{detail.data.editions?.length ?? 0} authorized edition metadata record(s).</p>
      <ul>{detail.data.editions?.map((edition) => <li key={edition.edition_id}><strong><bdi dir="ltr">{edition.edition_designation}</bdi></strong>{edition.official_publication_identifier ? <span> · <bdi dir="ltr">{edition.official_publication_identifier}</bdi></span> : null}<code dir="ltr">{edition.edition_id}</code>{edition.standing_history?.length ? <ol aria-label={`Standing history for ${edition.edition_designation}`}>{edition.standing_history.map((observation) => <li key={observation.version}><StandardsStatePresentation state={observation.standing} /><small>Observed {new Date(observation.observed_effective_at).toLocaleString()} · version {observation.version}</small></li>)}</ol> : <small>No standing observation is available.</small>}</li>)}</ul>
      <small>Metadata does not grant source-content rights or make this standard applicable to a Project.</small>
    </article>}</div> : null}
  </section>;
}
