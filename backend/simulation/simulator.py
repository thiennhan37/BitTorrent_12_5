from __future__ import annotations

import random
from collections.abc import Generator
from typing import Any

from .config import SimulationConfig
from .initial_state import clone_initial_state, generate_initial_state
from .models import Peer, TransferRecord
from .network import NetworkModel
from .simpy_compat import Environment
from .strategies import build_strategy


class BitTorrentSimulator:
    """Event-based virtual-time simulator for BitTorrent-style chunk exchange.

    This simulator models bandwidth sharing dynamically.
    Active uploads/downloads divide peer bandwidth in real time.
    """

    def __init__(
        self,
        config: SimulationConfig | None = None,
        strategy: str = "randomFirst",
        initial_state: list[list[int]] | list[set[int]] | None = None,
    ) -> None:
        self.config = config or SimulationConfig()
        self.config.validate()

        self.strategy_key = strategy

        self.rng = random.Random(self.config.seed)

        self.strategy = build_strategy(strategy, self.rng)

        self.initial_state = (
            clone_initial_state(initial_state)
            if initial_state is not None
            else generate_initial_state(self.config)
        )

        self.env = Environment()

        self.network = NetworkModel(self.config)

        self.peers = self._build_peers(self.initial_state)

        self.logs: list[dict[str, Any]] = []

        self.transfer_records: list[TransferRecord] = []

        self.progress_timeline: list[dict[str, Any]] = []

        self.transfer_counter = 0

        self.completed = False

        self.total_completion_time: float | None = None

    def _build_peers(self, initial_state: list[list[int]]) -> list[Peer]:
        peers: list[Peer] = []

        for peer_id in range(self.config.peer_count):
            chunks = (
                set(initial_state[peer_id])
                if peer_id < len(initial_state)
                else set()
            )

            peers.append(
                Peer(
                    id=peer_id,
                    owned_chunks=chunks,
                    download_bandwidth_kbps=self.config.bandwidth_kbps,
                    upload_bandwidth_kbps=self.config.effective_upload_bandwidth_kbps,
                    latency_ms=self.config.latency_ms,
                    max_download_slots=self.config.max_download_slots,
                    max_upload_slots=self.config.max_upload_slots,
                )
            )

        return peers

    def all_complete(self) -> bool:
        return all(
            peer.is_complete(self.config.total_chunks)
            for peer in self.peers
        )

    def chunk_availability(self) -> dict[int, int]:
        return {
            chunk_id: sum(
                1
                for peer in self.peers
                if peer.has_chunk(chunk_id)
            )
            for chunk_id in range(self.config.total_chunks)
        }

    def _progress_snapshot(self) -> dict[str, Any]:
        peer_snapshots = [
            peer.to_dict(self.config.total_chunks)
            for peer in self.peers
        ]

        average = round(
            sum(peer["completion"] for peer in peer_snapshots)
            / len(peer_snapshots),
            2,
        )

        return {
            "time": round(float(self.env.now), 6),
            "averageCompletion": average,
            "completedPeers": sum(
                1
                for peer in self.peers
                if peer.is_complete(self.config.total_chunks)
            ),
            "peers": peer_snapshots,
        }

    def _record_progress(self) -> None:
        snapshot = self._progress_snapshot()

        if (
            not self.progress_timeline
            or self.progress_timeline[-1] != snapshot
        ):
            self.progress_timeline.append(snapshot)

    def _log_event(
        self,
        *,
        event: str,
        transfer_id: int,
        source: Peer,
        destination: Peer,
        chunk_id: int,
        start_time: float,
        duration: float,
        bandwidth: float,
        latency_ms: float,
    ) -> None:
        current_time = float(self.env.now)

        self.logs.append(
            {
                "transferId": transfer_id,
                "event": event,
                "time": round(current_time, 6),
                "timestamp": round(current_time, 6),
                "sourcePeer": source.id,
                "destinationPeer": destination.id,
                "chunkId": chunk_id,
                "startTime": round(start_time, 6),
                "endTime": (
                    round(start_time + duration, 6)
                    if event == "START"
                    else round(current_time, 6)
                ),
                "duration": round(duration, 6),
                "bandwidthKbps": round(bandwidth, 6),
                "latencyMs": round(latency_ms, 6),
            }
        )

    def _transfer(
        self,
        destination: Peer,
        source: Peer,
        chunk_id: int,
    ) -> Generator[Any, Any, None]:

        if not destination.can_start_download(chunk_id):
            yield self.env.timeout(self.config.polling_interval)
            return

        if not source.can_upload_to(destination, chunk_id):
            yield self.env.timeout(self.config.polling_interval)
            return

        destination.start_transfer_from(source, chunk_id)

        start_time = float(self.env.now)

        transfer_id = self.transfer_counter
        self.transfer_counter += 1

        latency_ms = max(
            source.latency_ms,
            destination.latency_ms,
        )

        remaining_kb = self.config.chunk_size_kb

        self._log_event(
            event="START",
            transfer_id=transfer_id,
            source=source,
            destination=destination,
            chunk_id=chunk_id,
            start_time=start_time,
            duration=0.0,
            bandwidth=0.0,
            latency_ms=latency_ms,
        )

        # simulate network latency first
        yield self.env.timeout(latency_ms / 1000.0)

        # dynamic bandwidth simulation
        step_time = 0.05  # 50ms virtual step

        while remaining_kb > 0:
            if self.completed:
                destination.finish_transfer_from(
                    source,
                    chunk_id,
                    success=False,
                )
                return

            if not source.has_chunk(chunk_id):
                destination.finish_transfer_from(
                    source,
                    chunk_id,
                    success=False,
                )
                return

            bandwidth = self.network.effective_transfer_bandwidth(
                source,
                destination,
            )

            if bandwidth <= 0:
                yield self.env.timeout(step_time)
                continue

            transferred_kb = bandwidth * step_time

            remaining_kb -= transferred_kb

            yield self.env.timeout(step_time)

        destination.finish_transfer_from(
            source,
            chunk_id,
            success=True,
        )

        end_time = float(self.env.now)

        actual_duration = end_time - start_time

        average_bandwidth = (
            self.config.chunk_size_kb / actual_duration
            if actual_duration > 0
            else 0.0
        )

        record = TransferRecord(
            transfer_id=transfer_id,
            source_peer=source.id,
            destination_peer=destination.id,
            chunk_id=chunk_id,
            start_time=start_time,
            end_time=end_time,
            duration=actual_duration,
            bandwidth_kbps=average_bandwidth,
            latency_ms=latency_ms,
        )

        self.transfer_records.append(record)

        self._log_event(
            event="END",
            transfer_id=transfer_id,
            source=source,
            destination=destination,
            chunk_id=chunk_id,
            start_time=start_time,
            duration=actual_duration,
            bandwidth=average_bandwidth,
            latency_ms=latency_ms,
        )

        self._record_progress()

        if self.all_complete() and not self.completed:
            self.completed = True
            self.total_completion_time = end_time

    def _peer_process(
        self,
        peer: Peer,
    ) -> Generator[Any, Any, None]:

        # deterministic startup staggering
        yield self.env.timeout(
            self.rng.uniform(
                0,
                self.config.polling_interval,
            )
        )

        while (
            not self.completed
            and not peer.is_complete(self.config.total_chunks)
        ):

            if not peer.has_free_download_slot():
                yield self.env.timeout(
                    self.config.polling_interval
                )
                continue

            chunk_id = self.strategy.select_chunk(
                peer,
                self.peers,
                self.config.total_chunks,
            )

            if chunk_id is None:
                yield self.env.timeout(
                    self.config.polling_interval
                )
                continue

            source = self.strategy.select_source(
                peer,
                self.peers,
                chunk_id,
            )

            if source is None:
                yield self.env.timeout(
                    self.config.polling_interval
                )
                continue

            yield from self._transfer(
                peer,
                source,
                chunk_id,
            )

    def run(self) -> dict[str, Any]:

        self._record_progress()

        if self.all_complete():
            self.completed = True
            self.total_completion_time = 0.0
            return self.to_result()

        for peer in self.peers:
            self.env.process(
                self._peer_process(peer)
            )

        self.env.run(
            until=self.config.max_virtual_time
        )

        if (
            not self.completed
            and self.all_complete()
        ):
            self.completed = True
            self.total_completion_time = float(self.env.now)

        return self.to_result()

    def to_result(self) -> dict[str, Any]:

        total_time = (
            self.total_completion_time
            if self.total_completion_time is not None
            else float(self.env.now)
        )

        final_peers = [
            peer.to_dict(self.config.total_chunks)
            for peer in self.peers
        ]

        return {
            "strategy": self.strategy.key,
            "strategyName": self.strategy.display_name,
            "status": (
                "completed"
                if self.completed
                else "incomplete"
            ),
            "completed": self.completed,
            "totalTime": round(total_time, 6),
            "totalTransfers": len(self.transfer_records),
            "logs": self.logs,
            "transfers": [
                record.to_dict()
                for record in self.transfer_records
            ],
            "progressTimeline": self.progress_timeline,
            "initialState": clone_initial_state(
                self.initial_state
            ),
            "finalPeers": final_peers,
            "chunkAvailability": self.chunk_availability(),
            "config": self.config.to_dict(),
        }