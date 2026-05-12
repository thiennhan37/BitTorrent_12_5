from __future__ import annotations

from simulation.config import SimulationConfig
from simulation.initial_state import generate_initial_state
from simulation.service import compare_strategies
from simulation.simulator import BitTorrentSimulator
from simulation.strategies import RarestFirstStrategy
import random


def test_default_config_has_40_chunks():
    config = SimulationConfig()
    assert config.file_size_mb == 10
    assert config.chunk_size_kb == 256
    assert config.total_chunks == 40
    assert config.peer_count == 10


def test_initial_state_is_complete_swarm_but_not_complete_peers():
    config = SimulationConfig(seed=7)
    state = generate_initial_state(config)
    all_chunks = set().union(*(set(chunks) for chunks in state))
    assert len(state) == 10
    assert all_chunks == set(range(40))
    assert all(len(chunks) > 0 for chunks in state)


def test_single_simulation_completes_all_peers():
    config = SimulationConfig(seed=11, bandwidth_kbps=1024, latency_ms=10)
    result = BitTorrentSimulator(config=config, strategy="rarestFirst").run()
    assert result["completed"] is True
    assert result["totalTime"] > 0
    assert all(peer["completion"] == 100.0 for peer in result["finalPeers"])
    assert any(log["event"] == "START" for log in result["logs"])
    assert any(log["event"] == "END" for log in result["logs"])


def test_compare_uses_identical_initial_state():
    config_payload = {"seed": 123, "bandwidthKbps": 1024, "latencyMs": 25}
    result = compare_strategies(config_payload)
    assert result["randomFirst"]["initialState"] == result["rarestFirst"]["initialState"]
    assert result["randomFirst"]["completed"] is True
    assert result["rarestFirst"]["completed"] is True
    assert result["winner"] in {"randomFirst", "rarestFirst", "tie"}


def test_rarest_strategy_picks_chunk_with_fewest_copies():
    from simulation.models import Peer

    peers = [
        Peer(id=0, owned_chunks={0}),
        Peer(id=1, owned_chunks={1}),
        Peer(id=2, owned_chunks={2}),
        Peer(id=3, owned_chunks={2}),
    ]
    downloader = peers[0]
    strategy = RarestFirstStrategy(random.Random(5))
    selected = strategy.select_chunk(downloader, peers, total_chunks=3)
    assert selected == 1
