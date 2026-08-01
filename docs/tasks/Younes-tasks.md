# Member 1 — Backend & CAMARA Integration

## Role

Backend Engineer

Responsible for exposing the Decision API and integrating CAMARA APIs.

---

# Objectives

- Build the REST API
- Integrate CAMARA APIs (or Mock APIs)
- Build the orchestration layer
- Return normalized telecom signals

---

# Tech Stack

- FastAPI
- Python
- Pydantic
- HTTPX
- PostgreSQL
- Docker

---

# Folder Structure

backend/
├── app/
│   ├── api/
│   │   └── decision.py
│   ├── camara/
│   │   ├── roaming.py
│   │   ├── sim_swap.py
│   │   ├── location.py
│   │   └── number_verification.py
│   ├── orchestrator/
│   │   └── decision_orchestrator.py
│   ├── models/
│   └── main.py

---

# Tasks

## Task 1

Create FastAPI project.

---

## Task 2

Implement

POST /v1/decision

Input

- customer_id
- phone_number
- amount
- country
- merchant
- merchant_type

---

## Task 3

Create CAMARA adapters

- Device Roaming
- SIM Swap
- Number Verification
- Device Location

Each adapter must return a normalized response.

---

## Task 4

Create Mock CAMARA APIs

If sandbox is unavailable:

- Return predefined JSON
- Simulate latency
- Simulate failures

---

## Task 5

Build Decision Orchestrator

Responsibilities

- Receive transaction
- Decide which CAMARA APIs to call
- Execute calls
- Aggregate responses
- Return feature object

---

## Task 6

Expose JSON to Risk Engine

Example

{
    "roaming": true,
    "country": "MA",
    "days_since_sim_swap": 240,
    "number_verified": true
}

---

# Deliverables

- Working REST API
- Swagger Documentation
- CAMARA Integration
- Mock APIs
- Docker Container
