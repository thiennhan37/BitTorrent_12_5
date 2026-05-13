from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Peer:
    id: int
    owned_chunks: set[int] = field(default_factory=set)
    download_bandwidth_kbps: float = 512.0  # KB/s
    upload_bandwidth_kbps: float = 512.0    # KB/s
    latency_ms: float = 50.0

    max_download_slots: int = 1
    max_upload_slots: int = 3

    # chunk_id -> source_peer_id
    active_downloads: dict[int, int] = field(default_factory=dict)

    # destination_peer_id -> chunk_id
    active_uploads: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.download_bandwidth_kbps <= 0:
            raise ValueError("download_bandwidth_kbps must be > 0")

        if self.upload_bandwidth_kbps <= 0:
            raise ValueError("upload_bandwidth_kbps must be > 0")

        if self.max_download_slots <= 0:
            raise ValueError("max_download_slots must be > 0")

        if self.max_upload_slots <= 0:
            raise ValueError("max_upload_slots must be > 0")

        if self.latency_ms < 0:
            raise ValueError("latency_ms must be >= 0")

    # =========================================================
    # Chunk ownership
    # =========================================================

    def has_chunk(self, chunk_id: int) -> bool:
        return chunk_id in self.owned_chunks

    def receive_chunk(self, chunk_id: int) -> None:
        self.owned_chunks.add(chunk_id)

    def missing_chunks(self, total_chunks: int) -> list[int]:
        return [
            chunk_id
            for chunk_id in range(total_chunks)
            if chunk_id not in self.owned_chunks
        ]

    def completion_percentage(self, total_chunks: int) -> float:
        if total_chunks <= 0:
            return 0.0

        return round(len(self.owned_chunks) * 100 / total_chunks, 2)

    def is_complete(self, total_chunks: int) -> bool:
        return len(self.owned_chunks) >= total_chunks

    # =========================================================
    # Slot state
    # =========================================================

    def upload_count(self) -> int:
        return len(self.active_uploads)

    def download_count(self) -> int:
        return len(self.active_downloads)

    def has_free_download_slot(self) -> bool:
        return self.download_count() < self.max_download_slots

    def has_free_upload_slot(self) -> bool:
        return self.upload_count() < self.max_upload_slots

    # =========================================================
    # Dynamic bandwidth sharing
    # =========================================================

    def effective_upload_bandwidth(self) -> float:
        """
        Upload bandwidth shared equally across active uploads.
        """

        active = self.upload_count()

        if active <= 0:
            return self.upload_bandwidth_kbps

        return self.upload_bandwidth_kbps / active

    def effective_download_bandwidth(self) -> float:
        """
        Download bandwidth shared equally across active downloads.
        """

        active = self.download_count()

        if active <= 0:
            return self.download_bandwidth_kbps

        return self.download_bandwidth_kbps / active

    def estimated_transfer_bandwidth_to(self, downloader: "Peer") -> float:
        """
        Effective transfer speed is limited by BOTH:
        - uploader shared upload bandwidth
        - downloader shared download bandwidth
        """

        return min(
            self.effective_upload_bandwidth(),
            downloader.effective_download_bandwidth(),
        )

    # =========================================================
    # Transfer validation
    # =========================================================

    def can_start_download(self, chunk_id: int) -> bool:
        return (
            self.has_free_download_slot()
            and not self.has_chunk(chunk_id)
            and chunk_id not in self.active_downloads
        )

    def can_upload_to(self, downloader: "Peer", chunk_id: int) -> bool:
        return (
            self.id != downloader.id
            and self.has_chunk(chunk_id)
            and self.has_free_upload_slot()
            and downloader.id not in self.active_uploads
        )

    # =========================================================
    # Transfer lifecycle
    # =========================================================

    def start_transfer_from(self, source: "Peer", chunk_id: int) -> None:
        if not self.can_start_download(chunk_id):
            raise RuntimeError(
                f"Peer {self.id} cannot start download for chunk {chunk_id}"
            )

        if not source.can_upload_to(self, chunk_id):
            raise RuntimeError(
                f"Peer {source.id} cannot upload chunk "
                f"{chunk_id} to peer {self.id}"
            )

        self.active_downloads[chunk_id] = source.id
        source.active_uploads[self.id] = chunk_id

    def finish_transfer_from(
        self,
        source: "Peer",
        chunk_id: int,
        success: bool = True,
    ) -> None:
        actual_source_id = self.active_downloads.get(chunk_id)
        actual_chunk_id = source.active_uploads.get(self.id)

        if actual_source_id != source.id:
            raise RuntimeError(
                f"Transfer source mismatch for chunk {chunk_id}: "
                f"expected {actual_source_id}, got {source.id}"
            )

        if actual_chunk_id != chunk_id:
            raise RuntimeError(
                f"Transfer chunk mismatch for peer {self.id}: "
                f"expected {actual_chunk_id}, got {chunk_id}"
            )

        try:
            if success:
                self.receive_chunk(chunk_id)

        finally:
            self.active_downloads.pop(chunk_id, None)
            source.active_uploads.pop(self.id, None)

    # =========================================================
    # Serialization
    # =========================================================

    def to_dict(self, total_chunks: int) -> dict[str, Any]:
        return {
            "peerId": self.id,

            "ownedChunks": sorted(self.owned_chunks),

            "ownedChunkCount": len(self.owned_chunks),

            "missingChunkCount": max(
                total_chunks - len(self.owned_chunks),
                0,
            ),

            "completion": self.completion_percentage(total_chunks),

            "activeDownloads": dict(self.active_downloads),

            "activeUploads": dict(self.active_uploads),

            "uploadBandwidthKbps": round(
                self.upload_bandwidth_kbps,
                4,
            ),

            "downloadBandwidthKbps": round(
                self.download_bandwidth_kbps,
                4,
            ),

            "effectiveUploadBandwidthKbps": round(
                self.effective_upload_bandwidth(),
                4,
            ),

            "effectiveDownloadBandwidthKbps": round(
                self.effective_download_bandwidth(),
                4,
            ),
        }


@dataclass(slots=True)
class ActiveTransfer:
    transfer_id: int

    source_peer_id: int
    destination_peer_id: int

    chunk_id: int

    chunk_size_kb: float

    transferred_kb: float = 0.0

    start_time: float = 0.0

    last_update_time: float = 0.0

    completed: bool = False

    def remaining_kb(self) -> float:
        return max(self.chunk_size_kb - self.transferred_kb, 0.0)

    def progress_percentage(self) -> float:
        if self.chunk_size_kb <= 0:
            return 100.0

        return round(
            min(self.transferred_kb / self.chunk_size_kb, 1.0) * 100,
            2,
        )

    def advance(
        self,
        duration_seconds: float,
        bandwidth_kbps: float,
    ) -> float:
        """
        Advance transfer progress using current bandwidth.
        """

        if self.completed:
            return 0.0

        if duration_seconds <= 0:
            return 0.0

        transferred = duration_seconds * bandwidth_kbps

        actual = min(
            transferred,
            self.remaining_kb(),
        )

        self.transferred_kb += actual

        if self.transferred_kb >= self.chunk_size_kb:
            self.completed = True

        return actual

    def estimated_remaining_time(
        self,
        bandwidth_kbps: float,
    ) -> float:
        if bandwidth_kbps <= 0:
            return float("inf")

        return self.remaining_kb() / bandwidth_kbps

    def to_dict(self) -> dict[str, Any]:
        return {
            "transferId": self.transfer_id,

            "sourcePeerId": self.source_peer_id,

            "destinationPeerId": self.destination_peer_id,

            "chunkId": self.chunk_id,

            "chunkSizeKb": round(self.chunk_size_kb, 4),

            "transferredKb": round(self.transferred_kb, 4),

            "remainingKb": round(self.remaining_kb(), 4),

            "progressPercent": self.progress_percentage(),

            "completed": self.completed,

            "startTime": round(self.start_time, 6),

            "lastUpdateTime": round(self.last_update_time, 6),
        }


@dataclass(slots=True)
class TransferRecord:
    transfer_id: int

    source_peer: int
    destination_peer: int

    chunk_id: int

    start_time: float
    end_time: float

    duration: float

    bandwidth_kbps: float

    latency_ms: float

    transferred_kb: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "transferId": self.transfer_id,

            "sourcePeer": self.source_peer,

            "destinationPeer": self.destination_peer,

            "chunkId": self.chunk_id,

            "startTime": round(self.start_time, 6),

            "endTime": round(self.end_time, 6),

            "duration": round(self.duration, 6),

            "bandwidthKbps": round(self.bandwidth_kbps, 6),

            "latencyMs": round(self.latency_ms, 6),

            "transferredKb": round(self.transferred_kb, 6),
        }