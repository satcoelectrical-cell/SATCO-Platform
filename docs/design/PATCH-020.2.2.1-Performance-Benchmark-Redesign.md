# PATCH-020.2.2.1 Performance Benchmark Redesign

## Status

Approved

## Objective

Replace the existing performance benchmark implementation with a deterministic
benchmark harness that measures the authorized service boundary rather than
direct persistence operations.

## Principles

1. Dataset generation remains deterministic.
2. Read operations execute only through services.
3. Mutation benchmarks never reuse mutated entities.
4. Every measured sample is isolated.
5. Query counts are instrumented, never hardcoded.
6. Authorization and audit execution are included in measured operations.
7. Concurrency benchmarks use independent sessions only.

## Benchmark Structure

- Seed Corpus
- Read Benchmarks
- Mutation Benchmarks
- Concurrency Benchmarks
- Performance Report

## Non Goals

- No production changes.
- No repository optimization.
- No schema changes.
- No migration changes.
- No API changes.

## Exit Criteria

- Performance suite passes.
- No optimistic-version contamination.
- No transaction reuse.
- No ResourceClosedError.
- No RelationshipVersionConflict caused by benchmark reuse.
