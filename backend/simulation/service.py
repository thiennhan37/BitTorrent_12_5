from __future__ import annotations

from typing import Any, Mapping

from .config import SimulationConfig
from .initial_state import clone_initial_state, generate_initial_state
from .simulator import BitTorrentSimulator


def run_single_simulation(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(payload or {})
    strategy = payload.get("strategy", "randomFirst")
    config = SimulationConfig.from_payload(payload)
    initial_state = payload.get("initialState") or generate_initial_state(config)
    simulator = BitTorrentSimulator(config=config, strategy=strategy, initial_state=initial_state)
    return simulator.run()


def compare_strategies(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(payload or {})
    config = SimulationConfig.from_payload(payload)
    initial_state = clone_initial_state(payload.get("initialState") or generate_initial_state(config))

    random_first = BitTorrentSimulator(
        config=config,
        strategy="randomFirst",
        initial_state=clone_initial_state(initial_state),
    ).run()
    rarest_first = BitTorrentSimulator(
        config=config,
        strategy="rarestFirst",
        initial_state=clone_initial_state(initial_state),
    ).run()

    if not random_first["completed"] and not rarest_first["completed"]:
        winner = "none"
    elif random_first["completed"] and not rarest_first["completed"]:
        winner = "randomFirst"
    elif rarest_first["completed"] and not random_first["completed"]:
        winner = "rarestFirst"
    elif random_first["totalTime"] < rarest_first["totalTime"]:
        winner = "randomFirst"
    elif rarest_first["totalTime"] < random_first["totalTime"]:
        winner = "rarestFirst"
    else:
        winner = "tie"

    difference = round(abs(random_first["totalTime"] - rarest_first["totalTime"]), 6)
    return {
        "randomFirst": random_first,
        "rarestFirst": rarest_first,
        "winner": winner,
        "difference": difference,
        "initialState": initial_state,
        "config": config.to_dict(),
    }
