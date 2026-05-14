from __future__ import annotations
# import sys
# from pathlib import Path

# BACKEND_ROOT = Path(__file__).resolve().parents[1]
# if str(BACKEND_ROOT) not in sys.path:
#     sys.path.insert(0, str(BACKEND_ROOT))

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

# new github 
def test_compare_respects_initial_probability_payload():
    low_density = compare_strategies({"seed": 9, "initialChunkProbability": 0.15})
    higher_density = compare_strategies({"seed": 9, "initialChunkProbability": 0.30})

    assert low_density["config"]["initial_chunk_probability"] == 0.15
    assert higher_density["config"]["initial_chunk_probability"] == 0.30
    assert low_density["initialState"] != higher_density["initialState"]
    assert higher_density["randomFirst"]["totalTime"] != higher_density["rarestFirst"]["totalTime"]


def test_network_conditions_are_deterministic_but_source_dependent():
    from simulation.models import Peer
    from simulation.network import NetworkModel

    config = SimulationConfig(seed=9, bandwidth_kbps=512, latency_ms=50)
    network = NetworkModel(config)
    source_a = Peer(id=0, owned_chunks={0})
    source_b = Peer(id=1, owned_chunks={0})
    destination = Peer(id=2)

    first_duration = network.transfer_time(config.chunk_size_kb, source_a, destination)
    second_duration = network.transfer_time(config.chunk_size_kb, source_a, destination)
    other_source_duration = network.transfer_time(config.chunk_size_kb, source_b, destination)

    assert first_duration == second_duration
    assert first_duration != other_source_duration

def test_network_bandwidth_uses_active_transfer_counts():
    from simulation.models import Peer
    from simulation.network import NetworkModel

    config = SimulationConfig(seed=9, bandwidth_kbps=512, latency_ms=50)
    source = Peer(id=0, owned_chunks={0}, upload_bandwidth_kbps=512)
    destination = Peer(id=1, download_bandwidth_kbps=512)
    source.active_uploads[2] = 0
    destination.active_downloads[0] = 0

    bandwidth = NetworkModel(config).effective_bandwidth(source, destination)

    assert bandwidth > 0


def test_compare_api_returns_successful_result_envelope():
    from app import app

    response = app.test_client().post(
        "/api/simulate/compare",
        json={
            "seed": 9,
            "bandwidthKbps": 512,
            "latencyMs": 50,
            "initialChunkProbability": 0.15,
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["result"]["randomFirst"]["completed"] is True
    assert body["result"]["rarestFirst"]["completed"] is True

def test_peer_process_fills_multiple_download_slots():
    config = SimulationConfig(
        file_size_mb=1,
        chunk_size_kb=256,
        peer_count=4,
        seed=1,
        bandwidth_kbps=256,
        latency_ms=0,
        max_download_slots=3,
        max_upload_slots=3,
    )

    result = BitTorrentSimulator(
        config=config,
        strategy="rarestFirst",
        initial_state=[[0, 3], [1], [2], []],
    ).run()

    destination_three_starts = [
        log
        for log in result["logs"]
        if log["event"] == "START" and log["destinationPeer"] == 3
    ]
    first_start_time = destination_three_starts[0]["time"]
    simultaneous_starts = [
        log
        for log in destination_three_starts
        if log["time"] == first_start_time
    ]

    assert result["completed"] is True
    assert len(simultaneous_starts) == 3


def test_rarest_first_default_demo_is_not_slower_than_random_first():
    result = compare_strategies(
        {
            "seed": 9,
            "bandwidthKbps": 512,
            "latencyMs": 50,
            "initialChunkProbability": 0.15,
        }
    )

    assert result["rarestFirst"]["completed"] is True
    assert result["randomFirst"]["completed"] is True
    assert result["rarestFirst"]["totalTime"] <= result["randomFirst"]["totalTime"]