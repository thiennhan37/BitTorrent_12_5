from __future__ import annotations

from flask import Flask, jsonify, request

try:
    from flask_cors import CORS
except ModuleNotFoundError:  # pragma: no cover
    CORS = None

from simulation.config import SimulationConfig
from simulation.service import (
    compare_strategies,
    run_single_simulation,
)


def create_app() -> Flask:
    app = Flask(__name__)

    if CORS is not None:
        CORS(app)

    # ---------------------------------------------------------
    # Health check
    # ---------------------------------------------------------
    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "ok",
            }
        )

    # ---------------------------------------------------------
    # Default config
    # ---------------------------------------------------------
    @app.get("/api/config")
    def get_config():
        config = SimulationConfig()

        return jsonify(config.to_dict())

    # ---------------------------------------------------------
    # Single simulation
    # ---------------------------------------------------------
    @app.post("/api/simulate")
    def simulate():
        payload = request.get_json(silent=True)

        if payload is None:
            payload = {}

        try:
            result = run_single_simulation(payload)

            return jsonify(
                {
                    "success": True,
                    "result": result,
                }
            )

        except ValueError as exc:
            return jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "type": "validation_error",
                }
            ), 400

        except Exception as exc:
            return jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "type": "simulation_error",
                }
            ), 500

    # ---------------------------------------------------------
    # Strategy comparison
    # ---------------------------------------------------------
    @app.post("/api/simulate/compare")
    def compare():
        payload = request.get_json(silent=True)

        if payload is None:
            payload = {}

        try:
            result = compare_strategies(payload)

            return jsonify(
                {
                    "success": True,
                    "result": result,
                }
            )

        except ValueError as exc:
            return jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "type": "validation_error",
                }
            ), 400

        except Exception as exc:
            return jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "type": "comparison_error",
                }
            ), 500

    # ---------------------------------------------------------
    # Global error handler
    # ---------------------------------------------------------
    @app.errorhandler(404)
    def not_found(_):
        return jsonify(
            {
                "success": False,
                "error": "Endpoint not found",
            }
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify(
            {
                "success": False,
                "error": "Method not allowed",
            }
        ), 405

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )