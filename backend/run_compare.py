from __future__ import annotations

import json

from simulation.service import compare_strategies


def build_summary(result: dict) -> dict:
    return {
        "randomFirst": {
            "totalTime": result["randomFirst"]["totalTime"],
            "totalTransfers": result["randomFirst"]["totalTransfers"],
            "completed": result["randomFirst"]["completed"],

            # New debug metrics
            "averageDownloadSpeed":
                result["randomFirst"].get("averageDownloadSpeed"),

            "averageUploadUtilization":
                result["randomFirst"].get("averageUploadUtilization"),

            "averageParallelTransfers":
                result["randomFirst"].get("averageParallelTransfers"),
        },

        "rarestFirst": {
            "totalTime": result["rarestFirst"]["totalTime"],
            "totalTransfers": result["rarestFirst"]["totalTransfers"],
            "completed": result["rarestFirst"]["completed"],

            # New debug metrics
            "averageDownloadSpeed":
                result["rarestFirst"].get("averageDownloadSpeed"),

            "averageUploadUtilization":
                result["rarestFirst"].get("averageUploadUtilization"),

            "averageParallelTransfers":
                result["rarestFirst"].get("averageParallelTransfers"),
        },

        "winner": result["winner"],
        "difference": result["difference"],
    }


if __name__ == "__main__":

    config = {
        "seed": 9,
        "bandwidthKbps": 512,
        "latencyMs": 50,
        "initialChunkProbability": 0.15,

        # IMPORTANT:
        # allow parallel transfers to verify bandwidth sharing
        "maxDownloadSlots": 3,
        "maxUploadSlots": 3,
    }

    result = compare_strategies(config)

    summary = build_summary(result)

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )