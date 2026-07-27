from __future__ import annotations

import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import event


@dataclass(slots=True)
class Measurement:
    p95_ms: float
    mean_ms: float
    minimum_ms: float
    maximum_ms: float
    queries: int


class QueryCounter:
    def __init__(self, engine):
        self.engine = engine
        self.count = 0

    def _before_cursor_execute(
        self,
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        self.count += 1

    def __enter__(self):
        self.count = 0
        event.listen(
            self.engine,
            "before_cursor_execute",
            self._before_cursor_execute,
        )
        return self

    def __exit__(self, exc_type, exc, tb):
        event.remove(
            self.engine,
            "before_cursor_execute",
            self._before_cursor_execute,
        )


class PerformanceHarness:

    def __init__(
        self,
        *,
        engine,
        warmups: int = 5,
        samples: int = 30,
    ):
        self.engine = engine
        self.warmups = warmups
        self.samples = samples

    def measure(
        self,
        operation: Callable[[], None],
    ) -> Measurement:

        for _ in range(self.warmups):
            operation()

        durations = []

        with QueryCounter(self.engine) as counter:

            for _ in range(self.samples):

                started = time.perf_counter()

                operation()

                durations.append(
                    (time.perf_counter() - started) * 1000
                )

        ordered = sorted(durations)

        p95 = ordered[
            int(len(ordered) * 0.95) - 1
        ]

        return Measurement(
            p95_ms=p95,
            mean_ms=statistics.mean(durations),
            minimum_ms=min(durations),
            maximum_ms=max(durations),
            queries=counter.count // self.samples,
        )
