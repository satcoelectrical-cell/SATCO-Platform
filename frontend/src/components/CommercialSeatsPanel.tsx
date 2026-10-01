import { useEffect, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ApiResult, CommercialSeatList } from "../api/types";
import { EmptyState, ErrorState, LoadingState, ProtectedState, StatusBadge } from "./States";

function isSeatList(value: CommercialSeatList): boolean {
  return Number.isInteger(value?.capacity) && Number.isInteger(value?.consuming_count) && typeof value?.over_capacity === "boolean" && Array.isArray(value?.seats);
}

export function CommercialSeatsPanel({ onStepUpRequired }: { onStepUpRequired?: () => void }) {
  const [result, setResult] = useState<ApiResult<CommercialSeatList> | null>(null);
  const [selectedRetained, setSelectedRetained] = useState<number[]>([]);
  const [assignUserId, setAssignUserId] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const next = await api.commercialSeats();
    setResult(next);
    if (next.state === "success" && isSeatList(next.data)) setSelectedRetained(next.data.seats.filter((seat) => seat.state === "RETAINED").map((seat) => seat.user_id));
  };
  useEffect(() => { void load(); }, []);

  function handleStepUp() {
    setMessage("Recent administrator authentication is required. Confirm it in Sensitive security administration, then retry this action.");
    onStepUpRequired?.();
  }

  async function finishMutation(operation: () => ReturnType<typeof api.assignCommercialSeat>, success: string) {
    setBusy(true);
    const response = await operation();
    setBusy(false);
    if (response.state === "step_up_required") return handleStepUp();
    if (response.state !== "success") {
      setMessage(response.state === "conflict" ? "The server rejected the seat change against current entitlement or capacity state." : response.state === "unavailable" ? "Commercial seat administration is temporarily unavailable." : "The seat change was not accepted in the current authorized context.");
      return;
    }
    setMessage(success);
    await load();
  }

  async function assign(event: FormEvent) {
    event.preventDefault();
    const userId = Number(assignUserId);
    if (!Number.isInteger(userId) || userId <= 0) {
      setMessage("Enter a valid current-Organization member identifier.");
      return;
    }
    await finishMutation(() => api.assignCommercialSeat(userId), "The server assigned the commercial seat.");
    setAssignUserId("");
  }

  async function release(userId: number, displayName: string | null) {
    if (!window.confirm(`Release the commercial seat for ${displayName || `user ${userId}`}?`)) return;
    await finishMutation(() => api.releaseCommercialSeat(userId), "The server released the commercial seat.");
  }

  async function retainExactSet() {
    if (!window.confirm("Replace the retained-seat set with exactly the selected users? The server will decide whether capacity is resolved.")) return;
    setBusy(true);
    const response = await api.retainCommercialSeats([...selectedRetained].sort((a, b) => a - b));
    setBusy(false);
    if (response.state === "step_up_required") return handleStepUp();
    if (response.state !== "success") {
      setMessage(response.state === "conflict" ? "The server did not accept that exact retained-seat set." : response.state === "unavailable" ? "Commercial seat reconciliation is temporarily unavailable." : "Seat reconciliation was not accepted in the current authorized context.");
      return;
    }
    setMessage(response.data.unresolved ? "The server accepted the set, but over-capacity remains unresolved." : "The server accepted the exact retained-seat set and resolved over-capacity.");
    await load();
  }

  const seats = result?.state === "success" && isSeatList(result.data) ? result.data : null;
  const toggleRetained = (userId: number) => setSelectedRetained((current) => current.includes(userId) ? current.filter((item) => item !== userId) : [...current, userId]);

  return <section className="surface commercial-panel" aria-labelledby="commercial-seats-title">
    <div className="surface-header"><h2 id="commercial-seats-title">Commercial seats</h2><p>Capacity, consuming count, seat state, and executable status are returned by the server for the current Organization.</p></div>
    {!result ? <LoadingState label="Loading server-derived commercial seats…" /> : result.state === "protected" || result.state === "invalid" ? <ProtectedState /> : result.state !== "success" || !seats ? <ErrorState retry={() => void load()} unavailable={result.state === "unavailable"} /> : <>
      <div className="commercial-seat-summary"><div><strong>{seats.consuming_count}</strong><span>Consuming</span></div><div><strong>{seats.capacity}</strong><span>Server capacity</span></div><StatusBadge value={seats.over_capacity ? "OVER_CAPACITY" : "WITHIN_CAPACITY"} /></div>
      <form className="bootstrap-form commercial-seat-assign" onSubmit={assign}><label>Current-Organization member ID<input aria-label="Current-Organization member ID" inputMode="numeric" value={assignUserId} onChange={(event) => setAssignUserId(event.target.value.replace(/\D/g, ""))} required /></label><button className="button secondary" disabled={busy || !assignUserId}>Assign seat</button></form>
      {!seats.seats.length ? <EmptyState title="No commercial seats" detail="No current Organization members have a server-returned commercial seat state." /> : <div className="commercial-seat-list">{seats.seats.map((seat) => <article key={seat.user_id}><div><strong>{seat.display_name || `User ${seat.user_id}`}</strong><span>User ID {seat.user_id}</span></div><StatusBadge value={seat.state} /><StatusBadge value={seat.executable ? "EXECUTABLE" : "NOT_EXECUTABLE"} /><button type="button" className="button ghost compact" disabled={busy} onClick={() => void release(seat.user_id, seat.display_name)}>Release</button></article>)}</div>}
      {seats.over_capacity ? <fieldset className="commercial-retained"><legend>Exact retained-seat set</legend><p>The server reported over-capacity. Select the complete set to retain; no winner is chosen automatically and the server remains the capacity authority.</p>{seats.seats.map((seat) => <label key={seat.user_id}><input type="checkbox" checked={selectedRetained.includes(seat.user_id)} onChange={() => toggleRetained(seat.user_id)} />{seat.display_name || `User ${seat.user_id}`} <span>({seat.state})</span></label>)}<button type="button" className="button primary" disabled={busy} onClick={() => void retainExactSet()}>Submit exact retained set</button></fieldset> : null}
    </>}
    {message ? <p className="form-message" role="status">{message}</p> : null}
  </section>;
}
