"""Real-contract harness for the authoritative Batch-1 vector slice."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sqlalchemy import text

from .conformance_manifest import (
    BATCH_ONE_EXPECTED_RESULTS, BATCH_ONE_VECTOR_IDS,
    build_batch_one_manifest, validate_batch_one_manifest,
)


@dataclass(frozen=True, slots=True)
class VectorExecution:
    vector_id: str
    assertions_executed: int
    postgres_version: str


def load_batch_one_fixtures(directory: Path):
    files = {path.name.removesuffix(".fixture.v1.json"): path for path in directory.glob("*.fixture.v1.json")}
    if set(files) != set(BATCH_ONE_VECTOR_IDS):
        raise ValueError("fixture paths must equal the exact Batch-1 manifest")
    payloads = {}
    digests = {}
    for vector_id in BATCH_ONE_VECTOR_IDS:
        path = files[vector_id]
        raw = path.read_bytes()
        value = json.loads(raw)
        if set(value) != {"schema_version", "vector_id", "action", "expected"}:
            raise ValueError(f"noncanonical fixture shape: {vector_id}")
        if value["schema_version"] != 1 or value["vector_id"] != vector_id:
            raise ValueError(f"fixture identity mismatch: {vector_id}")
        if value["expected"] != BATCH_ONE_EXPECTED_RESULTS[vector_id]:
            raise ValueError(f"fixture expected result mismatch: {vector_id}")
        payloads[vector_id] = value
        digests[vector_id] = hashlib.sha256(raw).hexdigest()
    manifest = build_batch_one_manifest(digests)
    validate_batch_one_manifest(manifest)
    return payloads, manifest


class ConformanceHarness:
    def __init__(self, *, db_session, executors: dict[str, Callable[[dict], int]]):
        self.db_session = db_session
        self.executors = executors

    def execute(self, vector, fixture) -> VectorExecution:
        if vector.vector_id != fixture["vector_id"]:
            raise AssertionError("vector/fixture identity mismatch")
        executor = self.executors.get(vector.vector_id)
        if executor is None:
            raise AssertionError(f"no mapped assertion executor: {vector.vector_id}")
        postgres_version = self.db_session.execute(text("SHOW server_version")).scalar_one()
        count = executor(fixture)
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise AssertionError(f"vector executed no mapped assertions: {vector.vector_id}")
        return VectorExecution(vector.vector_id, count, postgres_version)
