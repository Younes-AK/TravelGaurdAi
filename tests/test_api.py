from datetime import UTC, datetime

from fastapi.testclient import TestClient

from travelguard_ai.api.app import create_app
from travelguard_ai.api.dependencies import ServiceUnavailableError, get_services


def _payload():
    return {
        "transaction": {
            "transaction_id": "tx-api-1",
            "amount": 725.5,
            "currency": "USD",
            "merchant_country": "MA",
            "timestamp": datetime.now(UTC).isoformat(),
            "device_id": "dev-trusted",
            "ip_address": "1.2.3.4",
        },
        "customer_profile": {
            "customer_id": "cust-api-1",
            "home_country": "US",
            "trusted_devices": ["dev-trusted"],
            "last_sim_swap_days": 120,
            "travel_frequency": 5,
            "avg_transaction_amount": 110.0,
            "phone_number": "+15555550123",
        },
        "signals": {
            "location": {
                "provider": "bank-cache",
                "confidence": 0.95,
                "country": "US",
                "verified": True,
            }
        },
    }


def test_health_ready_and_openapi_docs_work():
    app = create_app()
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"

        openapi = client.get("/openapi.json")
        assert openapi.status_code == 200
        assert "/v1/decision" in openapi.json()["paths"]

        docs = client.get("/docs")
        assert docs.status_code == 200
        assert "swagger-ui" in docs.text.lower()


def test_decision_endpoint_runs_full_flow():
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/v1/decision", json=_payload(), headers={"x-request-id": "req-test-1"})

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "req-test-1"
    assert body["decision"] in {"APPROVE", "STEP_UP", "REJECT"}
    assert 0.0 <= body["risk_score"] <= 1.0
    assert 0.0 <= body["confidence"] <= 1.0
    assert isinstance(body["explanation"], list)
    assert "location" in body["signals_used"]
    assert body["latency_ms"] >= 0.0


def test_decision_endpoint_returns_400_for_domain_invalid_request():
    app = create_app()
    payload = _payload()
    payload["transaction"]["merchant_country"] = ""

    with TestClient(app) as client:
        response = client.post("/v1/decision", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "INVALID_REQUEST"


def test_decision_endpoint_returns_422_for_schema_validation_error():
    app = create_app()
    payload = _payload()
    payload["transaction"]["amount"] = -1

    with TestClient(app) as client:
        response = client.post("/v1/decision", json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"


def test_decision_endpoint_returns_503_when_services_are_unavailable():
    app = create_app()

    def unavailable_services():
        raise ServiceUnavailableError("MODEL_UNAVAILABLE", "TravelGuard AI model is unavailable")

    app.dependency_overrides[get_services] = unavailable_services

    with TestClient(app) as client:
        response = client.post("/v1/decision", json=_payload())

    assert response.status_code == 503
    assert response.json()["error"] == "MODEL_UNAVAILABLE"
