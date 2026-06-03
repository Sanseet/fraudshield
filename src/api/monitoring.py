from __future__ import annotations

import time
import threading
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Deque


@dataclass
class MetricsSnapshot:
    total_transactions      : int
    fraud_rate_pct          : float
    avg_fraud_score         : float
    avg_confidence_score    : float
    avg_latency_ms          : float
    p95_latency_ms          : float
    p99_latency_ms          : float
    decision_distribution   : dict
    transactions_last_1min  : int
    transactions_last_5min  : int
    uptime_seconds          : float
    error_count             : int
    error_rate_pct          : float

    def to_dict(self) -> dict:
        return asdict(self)


class MetricsCollector:

    WINDOW_SIZE = 1000   
    def __init__(self):
        self._lock          = threading.Lock()
        self._start_time    = time.time()

        self._total         : int   = 0
        self._fraud_count   : int   = 0
        self._error_count   : int   = 0

        self._scores        : Deque[float] = deque(maxlen=self.WINDOW_SIZE)
        self._latencies     : Deque[float] = deque(maxlen=self.WINDOW_SIZE)
        self._decisions     : defaultdict  = defaultdict(int)

        self._timestamps    : Deque[float] = deque(maxlen=self.WINDOW_SIZE)

    def record(self, fraud_score: float, decision: str,
               latency_ms: float, is_error: bool = False):
        with self._lock:
            self._total += 1
            self._timestamps.append(time.time())

            if is_error:
                self._error_count += 1
                return

            self._scores.append(fraud_score)
            self._latencies.append(latency_ms)
            self._decisions[decision] += 1

            if decision == "BLOCK" or fraud_score > 0.60:
                self._fraud_count += 1

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            now = time.time()
            total = self._total

            scores    = list(self._scores)
            latencies = list(self._latencies)
            decisions = dict(self._decisions)
            timestamps = list(self._timestamps)

        fraud_rate  = (self._fraud_count / total * 100) if total else 0.0
        avg_score   = float(sum(scores) / len(scores))    if scores    else 0.0
        avg_lat     = float(sum(latencies) / len(latencies)) if latencies else 0.0

        import numpy as np
        p95 = float(np.percentile(latencies, 95)) if latencies else 0.0
        p99 = float(np.percentile(latencies, 99)) if latencies else 0.0

        cutoff_1m = now - 60
        cutoff_5m = now - 300
        txn_1m = sum(1 for t in timestamps if t >= cutoff_1m)
        txn_5m = sum(1 for t in timestamps if t >= cutoff_5m)

        error_rate = (self._error_count / total * 100) if total else 0.0

        dist = {}
        total_decisions = sum(decisions.values())
        for k, v in decisions.items():
            dist[k] = {
                "count": v,
                "pct": round(v / total_decisions * 100, 1) if total_decisions else 0,
            }

        return MetricsSnapshot(
            total_transactions     = total,
            fraud_rate_pct         = round(fraud_rate, 3),
            avg_fraud_score        = round(avg_score, 4),
            avg_confidence_score   = round(1.0 - avg_score, 4),
            avg_latency_ms         = round(avg_lat, 3),
            p95_latency_ms         = round(p95, 3),
            p99_latency_ms         = round(p99, 3),
            decision_distribution  = dist,
            transactions_last_1min = txn_1m,
            transactions_last_5min = txn_5m,
            uptime_seconds         = round(now - self._start_time, 1),
            error_count            = self._error_count,
            error_rate_pct         = round(error_rate, 3),
        )


_collector: MetricsCollector | None = None

def get_metrics() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
