from __future__ import annotations

from dataclasses import dataclass

from .config import SimulationConfig
from .models import Peer


@dataclass(slots=True)
class NetworkModel:
    config: SimulationConfig

    # =========================================================
    # Stable deterministic per-link random
    # =========================================================

    def _link_unit(self, source: Peer, destination: Peer, salt: int) -> float:
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

    # =========================================================
    # Link quality
    # =========================================================

    def link_bandwidth_factor(self, source: Peer, destination: Peer) -> float:
        """
        Stable bandwidth multiplier for each directed link.
        Range: 65% -> 135%
        """
        return 0.65 + self._link_unit(source, destination, salt=1) * 0.70

    def link_latency_factor(self, source: Peer, destination: Peer) -> float:
        """
        Stable latency multiplier for each directed link.
        Range: 75% -> 175%
        """
        return 0.75 + self._link_unit(source, destination, salt=2)

    # =========================================================
    # Effective network conditions
    # =========================================================

    def effective_latency_ms(self, source: Peer, destination: Peer) -> float:
        base_latency_ms = max(
            self.config.latency_ms,
            source.latency_ms,
            destination.latency_ms,
        )

        return base_latency_ms * self.link_latency_factor(source, destination)

    def effective_bandwidth(self, source: Peer, destination: Peer) -> float:
        """
        Bandwidth is shared across ALL active transfers.

        This fixes the unrealistic behavior where one peer could
        upload/download many chunks simultaneously at full speed.
        """
        # Number of active uploads/downloads. The peer stores the
        # active transfer state in dictionaries, so use the helper
        # methods to get numeric counts before applying max().
        upload_count = max(1, source.upload_count())
        download_count = max(1, destination.download_count())

        # Shared bandwidth
        shared_upload_bw = source.upload_bandwidth_kbps / upload_count
        shared_download_bw = destination.download_bandwidth_kbps / download_count


        # Base bottleneck bandwidth
        bandwidth = min(shared_upload_bw, shared_download_bw)

        # Per-link quality factor
        bandwidth *= self.link_bandwidth_factor(source, destination)

        # Prevent zero / absurdly tiny bandwidth
        return max(1.0, bandwidth)

    # =========================================================
    # Transfer timing
    # =========================================================
    def effective_transfer_bandwidth(
        self,
        source: Peer,
        destination: Peer,
    ) -> float:
        """
        Backward-compatible wrapper.

        Older simulator/service code still calls
        effective_transfer_bandwidth().
        """
        return self.effective_bandwidth(source, destination)
    
    def transfer_time(
        self,
        chunk_size_kb: int,
        source: Peer,
        destination: Peer,
    ) -> tuple[float, float, float]:
        """
        Returns:
            (
                duration_seconds,
                effective_bandwidth_kBps,
                latency_ms,
            )
        """

        bandwidth = self.effective_bandwidth(source, destination)

        latency_ms = self.effective_latency_ms(source, destination)

        transfer_seconds = chunk_size_kb / bandwidth

        duration = latency_ms / 1000.0 + transfer_seconds

        return duration, bandwidth, latency_ms