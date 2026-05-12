from __future__ import annotations

from dataclasses import dataclass

from .config import SimulationConfig
from .models import Peer


@dataclass(slots=True)
class NetworkModel:
    config: SimulationConfig

    def effective_bandwidth(self, source: Peer, destination: Peer) -> float:
        return min(source.upload_bandwidth_kbps, destination.download_bandwidth_kbps)

    def transfer_time(self, chunk_size_kb: int, source: Peer, destination: Peer) -> tuple[float, float, float]:
        """Return (duration_seconds, effective_bandwidth_KBps, latency_ms)."""

        bandwidth = self.effective_bandwidth(source, destination)
        latency_ms = max(self.config.latency_ms, source.latency_ms, destination.latency_ms)
        duration = latency_ms / 1000.0 + chunk_size_kb / bandwidth
        return duration, bandwidth, latency_ms
