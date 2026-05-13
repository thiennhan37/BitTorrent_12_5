from __future__ import annotations

from dataclasses import dataclass

from .config import SimulationConfig
from .models import Peer


@dataclass(slots=True)
class NetworkModel:
    config: SimulationConfig

# new github
    def _link_unit(self, source: Peer, destination: Peer, salt: int) -> float:
        """Return a stable 0..1 value for a directed source->destination link.

        The simulator runs each strategy in a separate process/environment when
        comparing them, so network conditions must not come from the mutable RNG
        sequence used by a strategy. This deterministic per-link value keeps the
        same seed, source, and destination under the same virtual network for
        Random-First and Rarest-First, while still making source choice matter.
        """

        value = (
            (self.config.seed + 1) * 1_000_003
            + (source.id + 1) * 91_193
            + (destination.id + 1) * 35_017
            + salt * 7_919
        ) & 0xFFFFFFFF
        value ^= value >> 16
        value = (value * 0x7FEB352D) & 0xFFFFFFFF
        value ^= value >> 15
        value = (value * 0x846CA68B) & 0xFFFFFFFF
        value ^= value >> 16
        return value / 0xFFFFFFFF

    def link_bandwidth_factor(self, source: Peer, destination: Peer) -> float:
        # Directed peer links vary between 65% and 135% of the configured base.
        # return 0.65 + self._link_unit(source, destination, salt=1) * 0.70
        base_bandwidth = min(source.upload_bandwidth_kbps, destination.download_bandwidth_kbps)
        return base_bandwidth * self.link_bandwidth_factor(source, destination)
    
    def effective_latency_ms(self, source: Peer, destination: Peer) -> float:
        base_latency_ms = max(self.config.latency_ms, source.latency_ms, destination.latency_ms)
        return base_latency_ms * self.link_latency_factor(source, destination)
    
    def link_latency_factor(self, source: Peer, destination: Peer) -> float:
        # Directed peer links vary between 75% and 175% of the configured base.
        return 0.75 + self._link_unit(source, destination, salt=2)
    def effective_bandwidth(self, source: Peer, destination: Peer) -> float:
        return min(source.upload_bandwidth_kbps, destination.download_bandwidth_kbps)

    def transfer_time(self, chunk_size_kb: int, source: Peer, destination: Peer) -> tuple[float, float, float]:
        """Return (duration_seconds, effective_bandwidth_KBps, latency_ms)."""

        bandwidth = self.effective_bandwidth(source, destination)
        
        # latency_ms = max(self.config.latency_ms, source.latency_ms, destination.latency_ms)
        latency_ms = self.effective_latency_ms(source, destination)
        
        duration = latency_ms / 1000.0 + chunk_size_kb / bandwidth
        return duration, bandwidth, latency_ms
