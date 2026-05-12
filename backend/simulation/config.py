from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from typing import Any, Mapping


@dataclass(slots=True)
class SimulationConfig:
    """Configuration shared by API, simulator, and tests.

    Notes:
        The assignment formula is `download_time = latency + chunk_size / bandwidth`.
        To keep that formula direct and easy to explain, bandwidth is stored as KB/s.
        The field name keeps `kbps` because the original project files already used it.
    """

    file_size_mb: int = 10
    chunk_size_kb: int = 256
    peer_count: int = 10
    seed: int = 9
    initial_chunk_probability: float = 0.15
    bandwidth_kbps: float = 512.0
    upload_bandwidth_kbps: float | None = None
    latency_ms: float = 50.0
    max_download_slots: int = 1
    max_upload_slots: int = 1
    polling_interval: float = 0.02
    max_virtual_time: float = 20_000.0

    @property
    def file_size_kb(self) -> int:
        return self.file_size_mb * 1024

    @property
    def total_chunks(self) -> int:
        return ceil(self.file_size_kb / self.chunk_size_kb)

    @property
    def effective_upload_bandwidth_kbps(self) -> float:
        return self.upload_bandwidth_kbps or self.bandwidth_kbps

    def validate(self) -> None:
        if self.file_size_mb <= 0:
            raise ValueError("file_size_mb must be > 0")
        if self.chunk_size_kb <= 0:
            raise ValueError("chunk_size_kb must be > 0")
        if self.peer_count <= 1:
            raise ValueError("peer_count must be > 1")
        if not 0 < self.initial_chunk_probability < 1:
            raise ValueError("initial_chunk_probability must be between 0 and 1")
        if self.bandwidth_kbps <= 0:
            raise ValueError("bandwidth_kbps must be > 0")
        if self.effective_upload_bandwidth_kbps <= 0:
            raise ValueError("upload_bandwidth_kbps must be > 0")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be >= 0")
        if self.max_download_slots <= 0:
            raise ValueError("max_download_slots must be > 0")
        if self.max_upload_slots <= 0:
            raise ValueError("max_upload_slots must be > 0")
        if self.polling_interval <= 0:
            raise ValueError("polling_interval must be > 0")
        if self.max_virtual_time <= 0:
            raise ValueError("max_virtual_time must be > 0")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.update(
            {
                "fileSizeKb": self.file_size_kb,
                "totalChunks": self.total_chunks,
                "effectiveUploadBandwidthKbps": self.effective_upload_bandwidth_kbps,
                "bandwidthUnit": "KB/s",
                "timeUnit": "seconds",
            }
        )
        return data

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> "SimulationConfig":
        payload = dict(payload or {})
        defaults = cls()

        def pick(*names: str, default: Any = None) -> Any:
            for name in names:
                if name in payload and payload[name] is not None:
                    return payload[name]
            return default

        config = cls(
            file_size_mb=int(pick("fileSizeMb", "file_size_mb", default=defaults.file_size_mb)),
            chunk_size_kb=int(pick("chunkSizeKb", "chunk_size_kb", default=defaults.chunk_size_kb)),
            peer_count=int(pick("peerCount", "peer_count", default=defaults.peer_count)),
            seed=int(pick("seed", default=defaults.seed)),
            initial_chunk_probability=float(
                pick(
                    "initialChunkProbability",
                    "initial_chunk_probability",
                    default=defaults.initial_chunk_probability,
                )
            ),
            bandwidth_kbps=float(
                pick("bandwidth", "bandwidthKbps", "bandwidth_kbps", default=defaults.bandwidth_kbps)
            ),
            upload_bandwidth_kbps=(
                None
                if pick("uploadBandwidth", "uploadBandwidthKbps", "upload_bandwidth_kbps", default=None)
                is None
                else float(
                    pick(
                        "uploadBandwidth",
                        "uploadBandwidthKbps",
                        "upload_bandwidth_kbps",
                        default=defaults.effective_upload_bandwidth_kbps,
                    )
                )
            ),
            latency_ms=float(pick("latency", "latencyMs", "latency_ms", default=defaults.latency_ms)),
            max_download_slots=int(
                pick("maxDownloadSlots", "max_download_slots", default=defaults.max_download_slots)
            ),
            max_upload_slots=int(pick("maxUploadSlots", "max_upload_slots", default=defaults.max_upload_slots)),
            polling_interval=float(pick("pollingInterval", "polling_interval", default=defaults.polling_interval)),
            max_virtual_time=float(pick("maxVirtualTime", "max_virtual_time", default=defaults.max_virtual_time)),
        )
        config.validate()
        return config
