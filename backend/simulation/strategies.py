from __future__ import annotations

import random
from abc import ABC, abstractmethod

from .models import Peer


class ChunkSelectionStrategy(ABC):
    key = "base"
    display_name = "Base Strategy"

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def eligible_sources(self, downloader: Peer, peers: list[Peer], chunk_id: int) -> list[Peer]:
        # Chi tra ve source dang co chunk va con upload slot tai thoi diem scheduler chay.
        return [peer for peer in peers if peer.can_upload_to(downloader, chunk_id)]

    def has_transfer_opportunity(self, downloader: Peer, peers: list[Peer], chunk_id: int) -> bool:
        # Mot chunk chi duoc chon neu downloader con slot, chua co/chua dang tai chunk do,
        # va ton tai it nhat mot uploader co the phuc vu ngay.
        return downloader.can_start_download(chunk_id) and bool(self.eligible_sources(downloader, peers, chunk_id))

    def select_source(self, downloader: Peer, peers: list[Peer], chunk_id: int) -> Peer | None:
        sources = self.eligible_sources(downloader, peers, chunk_id)
        if not sources:
            return None
        return self.rng.choice(sources)

    @abstractmethod
    def select_chunk(self, downloader: Peer, peers: list[Peer], total_chunks: int) -> int | None:
        raise NotImplementedError


class RandomFirstStrategy(ChunkSelectionStrategy):
    key = "randomFirst"
    display_name = "Random-First"

    def select_chunk(self, downloader: Peer, peers: list[Peer], total_chunks: int) -> int | None:
        if not downloader.has_free_download_slot():
            return None

        # Random-First: trong cac chunk co the tai ngay, chon ngau nhien.
        candidates = [
            chunk_id
            for chunk_id in downloader.missing_chunks(total_chunks)
            if self.has_transfer_opportunity(downloader, peers, chunk_id)
        ]
        if not candidates:
            return None
        return self.rng.choice(candidates)


class RarestFirstStrategy(ChunkSelectionStrategy):
    key = "rarestFirst"
    display_name = "Rarest-First"

    def select_chunk(self, downloader: Peer, peers: list[Peer], total_chunks: int) -> int | None:
        if not downloader.has_free_download_slot():
            return None

        # Rarest-First: uu tien chunk co it ban sao nhat trong toan swarm.
        # Van loc theo transfer opportunity de khong chon chunk khong co source ranh.
        availability: dict[int, int] = {}
        for chunk_id in downloader.missing_chunks(total_chunks):
            if not self.has_transfer_opportunity(downloader, peers, chunk_id):
                continue
            copies = sum(1 for peer in peers if peer.id != downloader.id and peer.has_chunk(chunk_id))
            if copies > 0:
                availability[chunk_id] = copies

        if not availability:
            return None

        rarest_count = min(availability.values())
        rarest_chunks = [chunk_id for chunk_id, count in availability.items() if count == rarest_count]
        return self.rng.choice(rarest_chunks)


def normalize_strategy_key(strategy: str) -> str:
    normalized = (strategy or "").replace("-", "").replace("_", "").lower()
    mapping = {
        "random": "randomFirst",
        "randomfirst": "randomFirst",
        "randomfirststrategy": "randomFirst",
        "rarest": "rarestFirst",
        "rarestfirst": "rarestFirst",
        "rarestfirststrategy": "rarestFirst",
    }
    if normalized not in mapping:
        raise ValueError("strategy must be one of: randomFirst, rarestFirst")
    return mapping[normalized]


def build_strategy(strategy: str, rng: random.Random) -> ChunkSelectionStrategy:
    key = normalize_strategy_key(strategy)
    if key == RandomFirstStrategy.key:
        return RandomFirstStrategy(rng)
    if key == RarestFirstStrategy.key:
        return RarestFirstStrategy(rng)
    raise ValueError(f"Unsupported strategy: {strategy}")
