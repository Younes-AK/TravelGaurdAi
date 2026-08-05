# TravelGuard AI Decision Service

TravelGuard AI is a demo-ready backend service for bank transaction risk decisions. It wraps the existing AI layer with a FastAPI API while preserving the current decision agent, XGBoost risk engine, feature builder, explainability, and CAMARA provider abstraction.

## What It Includes

- `POST /v1/decision` bank-facing transaction decision API
- `GET /health` liveness endpoint
- `GET /ready` readiness endpoint for model/provider availability
- Swagger UI and OpenAPI docs
- Request logging with request id, status code, decision, and latency
- Dependency injection with one initialized `DecisionAgent`, `RiskEngine`, `FeatureBuilder`, and CAMARA provider per app process
- Docker support for running the API

## Installation

Requires Python 3.12+.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Running Locally

```bash
uvicorn travelguard_ai.api.app:app --host 0.0.0.0 --port 8000 --reload
```

If you are running from the source tree without installing the package, set:

```bash
export PYTHONPATH=src
```

## Swagger

After starting the service, open:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Health: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/ready`

## Running Docker

```bash
docker build -t travelguard-ai .
docker run --rm -p 8000:8000 travelguard-ai
```

## Example Request

```bash
curl -X POST http://localhost:8000/v1/decision \
  -H "content-type: application/json" \
  -H "x-request-id: demo-request-1" \
  -d '{
    "transaction": {
      "transaction_id": "tx-2026-0001",
      "amount": 725.5,
      "currency": "USD",
      "merchant_country": "MA",
      "timestamp": "2026-08-05T12:30:00Z",
      "device_id": "device-123",
      "ip_address": "203.0.113.10"
    },
    "customer_profile": {
      "customer_id": "cust-001",
      "home_country": "US",
      "trusted_devices": ["device-123"],
      "last_sim_swap_days": 180,
      "travel_frequency": 4,
      "avg_transaction_amount": 110.0,
      "phone_number": "+15555550123"
    },
    "signals": {
      "location": {
        "provider": "bank-cache",
        "confidence": 0.92,
        "country": "MA",
        "verified": true
      }
    }
  }'
```

## Example Response

```json
{
  "decision": "STEP_UP",
  "risk_score": 0.4123,
  "confidence": 0.88,
  "explanation": [
    "medium_risk_score",
    "feature:amount_ratio_to_average:6.595",
    "feature:trusted_device:1.000"
  ],
  "signals_used": ["location", "roaming", "device_location", "sim_swap"],
  "camara_calls": ["roaming", "device_location", "sim_swap"],
  "latency_ms": 42.7,
  "request_id": "demo-request-1"
}
```

## Full Request Flow

```text
HTTP Request
  -> FastAPI request validation
  -> DecisionAgent
  -> CAMARA Provider abstraction
  -> FeatureBuilder
  -> XGBoost RiskEngine
  -> Explainability reasoning
  -> HTTP Response with decision, score, confidence, signals, and latency
```

## Error Responses

- `400 INVALID_REQUEST`: domain-level invalid request, such as missing merchant country
- `422 VALIDATION_ERROR`: schema validation error from FastAPI/Pydantic
- `503 MODEL_UNAVAILABLE`: model or service dependencies failed to initialize
- `503 PROVIDER_UNAVAILABLE`: CAMARA provider unavailable when surfaced by the provider layer
- `500 INFERENCE_ERROR`: unexpected inference failure

## Run Tests

```bash
pytest -q
```

## Project Layout

- `src/travelguard_ai` core AI package
- `src/travelguard_ai/api` FastAPI service layer
- `tests` unit and integration tests
- `pyproject.toml` packaging and tooling config
- `Dockerfile` API container
