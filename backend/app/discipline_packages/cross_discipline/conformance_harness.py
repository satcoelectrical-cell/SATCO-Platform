"""Real-contract harness for the authoritative Batch-1 vector slice."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sqlalchemy import text

from .conformance_manifest import (
    BATCH_ONE_EXPECTED_RESULTS, BATCH_ONE_VECTOR_IDS, BATCH_TWO_EXPECTED_RESULTS,
    BATCH_TWO_VECTOR_IDS, CUMULATIVE_BATCH_TWO_VECTOR_IDS,
    BATCH_THREE_EXPECTED_RESULTS, BATCH_THREE_VECTOR_IDS, CUMULATIVE_BATCH_THREE_VECTOR_IDS,
    BATCH_FOUR_EXPECTED_RESULTS, BATCH_FOUR_VECTOR_IDS, CUMULATIVE_BATCH_FOUR_VECTOR_IDS,
    BATCH_FIVE_EXPECTED_RESULTS, BATCH_FIVE_VECTOR_IDS, CUMULATIVE_BATCH_FIVE_VECTOR_IDS,
    build_batch_one_manifest, build_batch_two_manifest, validate_batch_one_manifest,
    build_batch_three_manifest, build_batch_four_manifest, build_batch_five_manifest,
)


@dataclass(frozen=True, slots=True)
class VectorExecution:
    vector_id: str
    assertions_executed: int
    postgres_version: str


def load_batch_one_fixtures(directory: Path):
    # Batch-1 replay consumes its immutable 51-vector subset even once the
    # directory also contains later accepted cumulative vectors.
    files = {
        path.name.removesuffix(".fixture.v1.json"): path
        for path in directory.glob("*.fixture.v1.json")
        if path.name.removesuffix(".fixture.v1.json") in BATCH_ONE_VECTOR_IDS
    }
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


def load_batch_two_fixtures(directory: Path):
    """Load the retained 51 fixtures plus the exact eight E↔I additions."""
    files = {
        path.name.removesuffix(".fixture.v1.json"): path
        for path in directory.glob("*.fixture.v1.json")
        if path.name.removesuffix(".fixture.v1.json") in CUMULATIVE_BATCH_TWO_VECTOR_IDS
    }
    if set(files) != set(CUMULATIVE_BATCH_TWO_VECTOR_IDS):
        raise ValueError("fixture paths must equal the exact cumulative Batch-2 manifest")
    expected = BATCH_ONE_EXPECTED_RESULTS | BATCH_TWO_EXPECTED_RESULTS
    payloads, digests = {}, {}
    for vector_id in CUMULATIVE_BATCH_TWO_VECTOR_IDS:
        raw = files[vector_id].read_bytes(); value = json.loads(raw)
        if set(value) != {"schema_version", "vector_id", "action", "expected"}:
            raise ValueError(f"noncanonical fixture shape: {vector_id}")
        if value["schema_version"] != 1 or value["vector_id"] != vector_id or value["expected"] != expected[vector_id]:
            raise ValueError(f"fixture identity mismatch: {vector_id}")
        payloads[vector_id] = value; digests[vector_id] = hashlib.sha256(raw).hexdigest()
    return payloads, build_batch_two_manifest(digests)


def load_batch_three_fixtures(directory: Path):
    """Load the retained 59 fixtures plus the exact eight I↔C additions."""
    files = {path.name.removesuffix(".fixture.v1.json"): path for path in directory.glob("*.fixture.v1.json")
             if path.name.removesuffix(".fixture.v1.json") in CUMULATIVE_BATCH_THREE_VECTOR_IDS}
    if set(files) != set(CUMULATIVE_BATCH_THREE_VECTOR_IDS):
        raise ValueError("fixture paths must equal the exact cumulative Batch-3 manifest")
    expected = BATCH_ONE_EXPECTED_RESULTS | BATCH_TWO_EXPECTED_RESULTS | BATCH_THREE_EXPECTED_RESULTS
    payloads, digests = {}, {}
    for vector_id in CUMULATIVE_BATCH_THREE_VECTOR_IDS:
        raw = files[vector_id].read_bytes(); value = json.loads(raw)
        if set(value) != {"schema_version", "vector_id", "action", "expected"}:
            raise ValueError(f"noncanonical fixture shape: {vector_id}")
        if value["schema_version"] != 1 or value["vector_id"] != vector_id or value["expected"] != expected[vector_id]:
            raise ValueError(f"fixture identity mismatch: {vector_id}")
        payloads[vector_id] = value; digests[vector_id] = hashlib.sha256(raw).hexdigest()
    return payloads, build_batch_three_manifest(digests)


def load_batch_four_fixtures(directory: Path):
    """Load the retained 67 fixtures plus the exact eight Electrical ↔ C&A additions."""
    files = {path.name.removesuffix(".fixture.v1.json"): path for path in directory.glob("*.fixture.v1.json")
             if path.name.removesuffix(".fixture.v1.json") in CUMULATIVE_BATCH_FOUR_VECTOR_IDS}
    if set(files) != set(CUMULATIVE_BATCH_FOUR_VECTOR_IDS):
        raise ValueError("fixture paths must equal the exact cumulative Batch-4 manifest")
    expected = BATCH_ONE_EXPECTED_RESULTS | BATCH_TWO_EXPECTED_RESULTS | BATCH_THREE_EXPECTED_RESULTS | BATCH_FOUR_EXPECTED_RESULTS
    payloads, digests = {}, {}
    for vector_id in CUMULATIVE_BATCH_FOUR_VECTOR_IDS:
        raw = files[vector_id].read_bytes(); value = json.loads(raw)
        if set(value) != {"schema_version", "vector_id", "action", "expected"}:
            raise ValueError(f"noncanonical fixture shape: {vector_id}")
        if value["schema_version"] != 1 or value["vector_id"] != vector_id or value["expected"] != expected[vector_id]:
            raise ValueError(f"fixture identity mismatch: {vector_id}")
        payloads[vector_id] = value; digests[vector_id] = hashlib.sha256(raw).hexdigest()
    return payloads, build_batch_four_manifest(digests)


def load_batch_five_fixtures(directory: Path):
    """Load the retained 75 fixtures plus the exact Batch-5 release vectors."""
    files = {path.name.removesuffix(".fixture.v1.json"): path for path in directory.glob("*.fixture.v1.json")
             if path.name.removesuffix(".fixture.v1.json") in CUMULATIVE_BATCH_FIVE_VECTOR_IDS}
    if set(files) != set(CUMULATIVE_BATCH_FIVE_VECTOR_IDS):
        raise ValueError("fixture paths must equal the exact cumulative Batch-5 manifest")
    expected = BATCH_ONE_EXPECTED_RESULTS | BATCH_TWO_EXPECTED_RESULTS | BATCH_THREE_EXPECTED_RESULTS | BATCH_FOUR_EXPECTED_RESULTS | BATCH_FIVE_EXPECTED_RESULTS
    payloads, digests = {}, {}
    for vector_id in CUMULATIVE_BATCH_FIVE_VECTOR_IDS:
        raw = files[vector_id].read_bytes(); value = json.loads(raw)
        if set(value) != {"schema_version", "vector_id", "action", "expected"}:
            raise ValueError(f"noncanonical fixture shape: {vector_id}")
        if value["schema_version"] != 1 or value["vector_id"] != vector_id or value["expected"] != expected[vector_id]:
            raise ValueError(f"fixture identity mismatch: {vector_id}")
        payloads[vector_id] = value; digests[vector_id] = hashlib.sha256(raw).hexdigest()
    return payloads, build_batch_five_manifest(digests)


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
