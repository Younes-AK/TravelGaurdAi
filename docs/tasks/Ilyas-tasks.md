# Member 2 — AI Risk Engine

## Role

AI / Decision Engineer

Responsible for fraud analysis, scoring, explainability, and decision generation.

---

# Objectives

- Build Risk Engine
- Calculate Risk Score
- Generate Explainable Decisions
- Return Decision JSON

---

# Tech Stack

- Python
- FastAPI
- Pydantic

(No ML required for MVP)

---

# Folder Structure

backend/
├── app/
│   ├── risk/
│   │   ├── scoring.py
│   │   ├── decision.py
│   │   ├── explain.py
│   │   └── weights.py

---

# Tasks

## Task 1

Design Feature Model

Input

- Roaming
- SIM Swap
- Number Verification
- Location
- Amount
- Merchant
- Country

---

## Task 2

Implement Risk Score

Example

Risk Score

0 → 100

---

## Task 3

Implement Decision Logic

Return

- APPROVE
- STEP_UP
- REJECT

based on thresholds.

---

## Task 4

Generate Explainable AI Output

Example

Approved because:

- Device is roaming
- SIM unchanged
- Customer is a frequent traveler
- Amount is normal

---

## Task 5

Return Final JSON

Example

{
    "decision": "APPROVE",
    "risk_score": 18,
    "confidence": "HIGH",
    "explanation": [
        "Roaming detected",
        "SIM stable",
        "Known travel behavior"
    ]
}

---

## Task 6

Create Demo Scenarios

Scenario 1

Tourist

↓

Approve

Scenario 2

Borderline

↓

Step-Up

Scenario 3

Fraud

↓

Reject

---

# Deliverables

- Risk Engine
- Decision Logic
- Explainability Engine
- Decision JSON
- Demo Scenarios
