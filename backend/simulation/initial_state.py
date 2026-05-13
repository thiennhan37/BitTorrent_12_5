from __future__ import annotations

import random

from .config import SimulationConfig


def generate_initial_state(config: SimulationConfig) -> list[list[int]]:
    """
    Generate deterministic peer -> chunk ownership for a given seed.

    Guarantees:
        1. Exactly `peer_count` peers are returned.
        2. Every chunk exists on at least one peer.
        3. Every peer starts with at least one chunk.
        4. No peer starts complete unless unavoidable.
        5. Returned lists are sorted and deterministic.
    """

    config.validate()

    rng = random.Random(config.seed)

    total_chunks = config.total_chunks
    peer_count = config.peer_count

    if total_chunks <= 0:
        raise ValueError("total_chunks must be > 0")

    if peer_count <= 0:
        raise ValueError("peer_count must be > 0")

    peer_chunks: list[set[int]] = [set() for _ in range(peer_count)]

    # ---------------------------------------------------------
    # First pass:
    # Random Bernoulli ownership distribution.
    # ---------------------------------------------------------
    for peer_id in range(peer_count):
        for chunk_id in range(total_chunks):
            if rng.random() < config.initial_chunk_probability:
                peer_chunks[peer_id].add(chunk_id)

    # ---------------------------------------------------------
    # Ensure every chunk exists at least once.
    # ---------------------------------------------------------
    for chunk_id in range(total_chunks):
        owners = [
            peer_id
            for peer_id, chunks in enumerate(peer_chunks)
            if chunk_id in chunks
        ]

        if not owners:
            selected_peer = rng.randrange(peer_count)
            peer_chunks[selected_peer].add(chunk_id)

    # ---------------------------------------------------------
    # Ensure every peer owns at least one chunk.
    # ---------------------------------------------------------
    for peer_id, chunks in enumerate(peer_chunks):
        if not chunks:
            chunk_id = rng.randrange(total_chunks)
            chunks.add(chunk_id)

    # ---------------------------------------------------------
    # Avoid peers starting with full file.
    # Keep at least one copy of every chunk in swarm.
    # ---------------------------------------------------------
    if total_chunks > 1:
        for peer_id, chunks in enumerate(peer_chunks):
            if len(chunks) == total_chunks:

                removable_chunks = []

                for chunk_id in chunks:
                    owner_count = sum(
                        1
                        for owner_chunks in peer_chunks
                        if chunk_id in owner_chunks
                    )

                    # only removable if another owner exists
                    if owner_count > 1:
                        removable_chunks.append(chunk_id)

                if removable_chunks:
                    removed_chunk = rng.choice(removable_chunks)
                    chunks.remove(removed_chunk)

    # ---------------------------------------------------------
    # Return deterministic sorted structure.
    # ---------------------------------------------------------
    return [
        sorted(chunks)
        for chunks in peer_chunks
    ]


def clone_initial_state(
    initial_state: list[list[int]] | list[set[int]],
) -> list[list[int]]:
    """
    Deep-clone initial state into deterministic sorted lists.

    Important:
        Prevents accidental mutation between simulations.
    """

    cloned_state: list[list[int]] = []

    for chunks in initial_state:
        unique_chunks = sorted(set(chunks))
        cloned_state.append(unique_chunks)

    return cloned_state