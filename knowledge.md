# TravelGuard AI — Build Knowledge Base

Single reference for implementation. Everything needed to build without
re-reading the PDFs. Deep API detail lives in
[`docs/network-apis-guide.md`](docs/network-apis-guide.md).

Sources: `docs/TravelGuard_AI_Idea_Phase.pdf`, `docs/TravelGuard_AI_Prototype_Phase.pdf`,
`docs/projectArch`, `docs/tasks/*.md`, CAMARA OpenAPI specs, Nokia NaC SDK v10.0.0.

---

## 1. What we are building

A **B2B decision-intelligence layer** that a bank's fraud engine calls before
blocking a cross-border card transaction. It answers the one question banking
data structurally cannot answer:

> Is this cardholder physically where the transaction says they are, right now?

We do **not** replace the fraud engine. We hand it a signal it cannot produce on
its own — a live, network-attested confirmation of the customer's location — and
return an advisory decision with an explanation. The bank keeps the final call
and the compliance ownership.

**The canonical story:** Ahmed, a German tourist, lands in Marrakech, taps his
card for a €4.20 coffee, and gets declined. Static rules (new country + high
amount + unknown merchant → BLOCK) stop fraud but punish honest travellers.
Travel notices don't fix it — customers forget, trips change, engines ignore them.

**Why the bank's existing proxies fail — by construction, not by accident:**

| What banks try today | Why it isn't evidence |
|---|---|
| Merchant / session IP address | Defeated by a VPN or the merchant's hosting location |
| GPS from the banking app | Requires the app open; trivially spoofable |
| Customer-set travel notice | Forgotten, incomplete, or ignored by the engine |

**The core technical claim, stated precisely:** network location is *attested by
the network*, not *reported by the device*. App GPS is a claim made by software
running on hardware an attacker may control. Network location is inferred from
which radio the SIM is actually attached to. That difference is the entire
product.

---

## 2. Architecture

```
Customer → Merchant/ATM → Acquirer → Visa/MC → Issuing Bank
                                                    │
                                          POST /v1/decision
                                                    ▼
                                    ┌───────────────────────────┐
                                    │  TravelGuard AI layer     │
                                    │  Orchestrator             │
                                    │  Feature builder          │
                                    │  Risk engine              │
                                    │  Explainer                │
                                    └───────────┬───────────────┘
                                                ▼
                            CAMARA APIs via Nokia Network-as-Code
                     Roaming · SIM Swap · Device Location · Number Verify
                                                │
                                                ▼
                              Decision + explanation → back to bank
```

Four layers, one synchronous call. **The bank never talks to CAMARA directly** —
orchestration, degradation, scoring and explanation all sit behind our boundary.

**Design principle:** every CAMARA call sits behind an adapter interface. Moving
from sandbox to a live operator gateway is a configuration change, not a rewrite.
Enforce this — no CAMARA-shaped types leak past the adapter layer.

### Repo layout

```
backend/
├── app/
│   ├── main.py
│   ├── api/decision.py              # POST /v1/decision
│   ├── camara/
│   │   ├── base.py                  # adapter interface + normalised types
│   │   ├── roaming.py
│   │   ├── sim_swap.py
│   │   ├── location.py
│   │   ├── number_verification.py
│   │   ├── mock.py                  # offline fixtures, latency + failure sim
│   │   └── sandbox_numbers.py       # test MSISDN → behaviour table
│   ├── orchestrator/decision_orchestrator.py
│   ├── risk/
│   │   ├── features.py              # feature vector assembly
│   │   ├── scoring.py
│   │   ├── weights.py
│   │   ├── fusion.py                # interaction rules
│   │   ├── decision.py              # thresholds → APPROVE/STEP_UP/REJECT
│   │   └── explain.py
│   └── models/                      # pydantic schemas
frontend/
└── src/
    ├── pages/{Dashboard,TransactionSimulator,DecisionDetails}.tsx
    ├── components/
    └── services/
```

### Ownership

| | Owner | Scope |
|---|---|---|
| Member 1 | **Younes** | FastAPI, `POST /v1/decision`, CAMARA adapters + mocks, orchestrator, Docker, Swagger |
| Member 2 | Ilyas | Risk engine — features, scoring, fusion, decision logic, explainability |
| Member 3 | Ahmad | React + TS + Tailwind + shadcn/ui + React Query dashboard, simulator, charts |

**Contract between 1 and 2** is the normalised feature object. Freeze it early —
it is the only coupling point and the thing most likely to cause a merge crisis
on demo day.

---

## 3. The integration contract

One endpoint. This is the bank's entire integration surface — deliberately
minimal, because integration effort is the main adoption barrier.

### Request

```http
POST /v1/decision
Authorization: Bearer <bank_api_key>
```
```json
{
  "transaction_id": "txn_8f21c",
  "msisdn": "+4915112345678",
  "amount": { "value": 4.20, "currency": "EUR" },
  "merchant": { "country": "MA", "category": "restaurant" },
  "customer_ref": "cust_00417"
}
```

### Response

```json
{
  "decision": "APPROVE",
  "risk_score": 18,
  "confidence": "high",
  "signals_used": ["roaming_status", "sim_swap"],
  "explanation": [
    "Active roaming detected in MA at time of transaction",
    "SIM unchanged for 247 days",
    "Customer has transacted in MA in 3 previous trips",
    "Amount is within this customer's normal range"
  ],
  "latency_ms": 412
}
```

**Two design decisions to defend:**

- **No raw PII crosses the boundary.** We receive an MSISDN and an opaque
  `customer_ref`. Behavioural features stay on the bank's side. We never hold
  names, card numbers, or addresses.
- **The response is advisory.** We return a recommendation plus justification.
  The bank executes. Regulatory responsibility stays where it already sits.

**`explanation` is a first-class field, not a log line.** It is what lets a
call-centre agent tell a customer why their payment stopped, and what a
regulator will ask to see. Any model we deploy must be able to produce it.

`signals_used` matters too — it is how we prove cost-aware orchestration to a
procurement reviewer.

---

## 4. Orchestration — cost-aware escalation

CAMARA calls are **billable**. We do not fire all four every time. The
orchestrator escalates only as far as the uncertainty requires:

| Step | Call | Trigger |
|---|---|---|
| 1 | **Roaming Status** | Always. Cheapest signal; resolves most clear-cut travel cases |
| 2 | **SIM Swap** | If roaming country matches merchant country — rule out takeover before approving |
| 3 | **Device Location** | If signals disagree, or amount is high — precise confirmation |
| 4 | **Number Verification** | If identity itself is in question — before any step-up is offered |

**Why this matters commercially:** paying for four API calls on every low-value
coffee purchase would not survive a procurement review. Paying for one, and
escalating only when genuinely ambiguous, will. Ahmed's coffee resolves in **two
calls** — Device Location is never queried because the evidence already converged.

### Latency budget

A payment authorisation will not wait. Every stage is bounded; if a stage
exceeds its allowance the engine proceeds with what it has rather than blocking
the transaction on its own slowness.

| Stage | Allowance | Behaviour on timeout |
|---|---|---|
| Request validation + profile lookup | ~50 ms | Fail closed — malformed requests rejected outright |
| CAMARA signal collection (**parallel**) | ~400 ms | Proceed with whichever signals returned; mark rest unavailable |
| Feature build + scoring | ~80 ms | Fall back to conservative rule overlay |
| Explanation generation | ~60 ms | Emit structured reason codes without narrative text |

Total ~590 ms. Implementation: `asyncio.gather(..., return_exceptions=True)`
with per-call `httpx` timeouts. **Never** let one slow adapter hold the response.

### Degradation strategy — the rule that defines the product

> Missing data is **uncertainty, not guilt**.

Absent signals widen the confidence interval and push borderline cases toward
**step-up**, never toward rejection. A network API can time out, return partial
data, or be unavailable for a given operator — none of that is evidence against
the customer. Getting this backwards would reproduce the exact failure the
product exists to fix.

---

## 5. The risk engine

### Feature vector

Network signals and bank context are combined into **one vector before any
scoring happens**. Neither source is sufficient alone.

| From the network | From the bank |
|---|---|
| Country match between device and merchant | Countries visited in last 24 months |
| Roaming state + time since roaming began | Amount relative to customer's own distribution |
| Days since last SIM change | Merchant category familiarity |
| Number-to-device binding confirmed | Time since last domestic transaction |
| Signal completeness score | Historical dispute / chargeback flags |

`signal_completeness` is what carries degradation into scoring — make it an
explicit feature, not an implicit branch.

### Fusion rules — the actual insight

These are **interaction effects**: the meaning of one signal is conditional on
another. A flat rule engine cannot express them.

| Signal combination | Naive reading | TravelGuard reading |
|---|---|---|
| Roaming in country + SIM swapped 1 day ago | Two signals, one good one neutral | **Takeover pattern — escalate sharply** |
| Roaming in country + SIM stable 8 months + frequent traveller | Foreign country, therefore suspicious | **Entirely normal for this customer — approve** |
| Location unavailable + roaming confirmed + small amount | Incomplete data, therefore block | **Enough evidence for a low-value approval** |
| Device at home + transaction abroad | Possible travel notice | **Card is being used where the customer is not** |

Read separately, `roaming = true` and `sim_swap = recent` both look acceptable.
Read together they describe a textbook SIM-swap takeover. That is the whole
argument for why this is decisioning and not an API wrapper.

### Thresholds

| Score | Decision | Meaning |
|---|---|---|
| **0–30** | `APPROVE` | Sufficient converging evidence. Customer experiences nothing at all |
| **31–70** | `STEP_UP` | Plausible but unconfirmed. Ask the customer, then decide with their answer as an input |
| **71–100** | `REJECT` | Evidence actively contradicts the transaction. Block and flag |

**Thresholds are configurable per bank** — risk appetite is a commercial
decision, not a technical one. A private bank and a prepaid travel-card issuer
will not sit at the same cut-off. Put them in config, not constants.

Beyond approve/reject, the engine can recommend step-up auth, additional
verification, or routing to manual review — always choosing the **least
disruptive action that still contains the risk**.

---

## 6. Demo scenarios — exact expected outputs

These are the acceptance tests. Hard-code them as fixtures; the frontend has a
button for each.

### Scenario 1 — `APPROVE`, risk 18
**Ahmed buys coffee in Marrakech.** `EUR 4.20 · restaurant · MA · German card`
- Roaming Status: roaming in MA, active for 6 hours
- SIM Swap: last change 247 days ago
- Profile: has travelled to MA on three previous occasions
- Amount: within his normal daily spend

→ **Two API calls were enough.** Device Location never queried — evidence had
already converged. The transaction the old rule engine would have blocked goes
through untouched.

### Scenario 2 — `STEP_UP`, risk 52
**First-time traveller, high-value purchase.** `EUR 1,850 · electronics · TR · no prior travel history`
- Roaming Status: roaming in TR, active for 40 minutes
- Device Location: confirmed in TR, escalated because of the amount
- SIM Swap: last change 12 days ago — recent, but not immediate
- Profile: no international transactions on record

→ The network says the customer is there. The behavioural baseline says nothing
like this has ever happened. Rather than guess, the engine asks: a push
confirmation is sent, and the answer feeds back into the decision.

### Scenario 3 — `REJECT`, risk 94
**SIM-swap takeover attempt.** `EUR 2,400 · money transfer · MA · card reported active at home`
- SIM Swap: SIM changed 14 hours ago
- Device Location: device is in the home country, not in MA
- Number Verification: binding could not be confirmed
- Merchant category: high-risk transfer, not typical for this customer

→ Every individual signal here would survive a threshold rule. Read together
they describe a textbook account takeover — precisely the case a location-only
check would have waved through.

---

## 7. CAMARA APIs — build essentials

Full detail in [`docs/network-apis-guide.md`](docs/network-apis-guide.md).

### Access model

Nokia ships Network-as-Code **through RapidAPI**. One RapidAPI key is the whole
credential; Nokia handles operator-side OAuth behind it.

```bash
pip install network_as_code   # v10.0.0 · Python ≥3.11 · deps: httpx + pydantic v2
```
Same stack as FastAPI — no dependency conflict.

```python
import os
from network_as_code import NetworkAsCodeApi

client = NetworkAsCodeApi(
    rapidapi_host="network-as-code.nokia.rapidapi.com",
    api_key=os.environ["NAC_API_KEY"],
)
```

Default environment is `https://network-as-code.p-eu.rapidapi.com`. The
generated reference is inconsistent about import casing — **`network_as_code` is
the real package name** (per `pyproject.toml`), not `networkAsCode`.

Sandbox devices are keyed by phone number (`+99999991000` and neighbours), each
pre-configured to return specific results including errors. Pin the full
number→behaviour table in `sandbox_numbers.py` before demo day.

Every method accepts `correlator` — **set it to our `transaction_id`**. Free
distributed tracing, and the right answer to "how would you debug this in
production?".

### The four calls

```python
from network_as_code.device_status import RetrieveRoamingStatusDeviceStatusRequestDevice
from network_as_code.location import VerifyLocationRequestDevice, VerifyLocationRequestArea

# 1 — always
roaming = client.device_status.retrieve_roaming_status(
    device=RetrieveRoamingStatusDeviceStatusRequestDevice(phone_number=msisdn),
    correlator=transaction_id,
)
# → roaming: bool · countryCode: int (MCC) · countryName: str[] · lastStatusTime: RFC3339

# 2 — days-since, NOT the boolean form
sim = client.sim_swap.retrieve_date(phone_number=msisdn, correlator=transaction_id)
# → latestSimChange: RFC3339 · monitoredPeriod: int (days)

# 3 — only when signals disagree or amount is high
loc = client.location.verify(
    device=VerifyLocationRequestDevice(phone_number=msisdn),
    area=VerifyLocationRequestArea(
        area_type="CIRCLE",
        center={"latitude": 31.6295, "longitude": -7.9811},
        radius=50000,
    ),
    max_age=3600,
)
# → verificationResult: TRUE|FALSE|PARTIAL · lastLocationTime · matchRate (1-99, PARTIAL only)

# 4 — three-legged; step-up channel, not inline
verified = client.number_verification.verify(phone_number=msisdn)
# → devicePhoneNumberVerified: bool
```

### Gotchas that will bite

**Call `sim_swap.retrieve_date`, not `check`.** Our fusion rules need *days
since change* as a continuous feature — "swapped 1 day ago" and "swapped 200
days ago" mean opposite things. `check` collapses that to a boolean and destroys
the signal. (`check` takes `max_age` in **hours**, min 1, max 2400, default 240.)

**`verificationResult` has three values, not two.** `PARTIAL` means the
network's uncertainty region overlaps the requested circle. Mapping
`PARTIAL → FALSE` manufactures false positives — the exact failure we exist to
fix. Map to a graded feature (`matchRate / 100`) and let fusion weigh it.

**`countryName` is an array and can be empty** on a *successful* call — an MCC
may map to several countries or none. `resp["countryName"][0]` will crash in
production. Normalise to `Optional[str]` in the adapter.

**Unit mismatch.** SimSwap `maxAge` = **hours**. Location `maxAge` = **seconds**.
Location `radius` = **metres**, min 1. Normalise at the adapter boundary; never
let raw units reach the risk engine.

**Location 422s are "don't know", never "lying".** `UNABLE_TO_LOCATE`,
`AREA_NOT_COVERED`, `UNABLE_TO_FULFILL_MAX_AGE`, `INVALID_AREA` — all widen
uncertainty and push toward step-up. Never toward reject.

**Number Verification cannot be inline.** It requires a three-legged token from
mobile-network authentication (auth code or CIBA, poll mode only), single-use,
no refresh, max 5-minute lifetime, and the device must be on mobile data. There
is no user device in the loop when a card is tapped at a café till. So it is a
**step-up channel**: the bank pushes to its app, the app completes network auth,
the result feeds back as a decision input. Consistent with Scenario 2 — but the
dashboard must not imply it happens inside the 400 ms budget. An operator on the
judging panel will catch that.

**Two-legged vs three-legged identifier rules.** With a three-legged token,
sending `phoneNumber` in the body is `422 UNNECESSARY_IDENTIFIER`. With
two-legged, omitting it is `422 MISSING_IDENTIFIER`.

**Pin API versions.** Several CAMARA specs on `main` are marked `vwip`. Use the
released paths (`v1`/`v2`/`v3`) from repo Releases — WIP schemas change under you.

### Mock layer requirements

The mock adapters are not a fallback, they are the primary dev surface. They must:
- Return normalised responses identical in shape to the live adapters
- **Simulate latency** — otherwise the whole latency-budget design is untested
- **Simulate failures and timeouts** — degradation is a headline feature and
  needs to be demonstrable on demand
- Drive all three demo scenarios deterministically

Build the degradation path against mocks from day one. A demo where a signal is
deliberately killed live, and the engine still returns a sane step-up with an
honest explanation, is worth more than any slide.

---

## 8. What we claim, and what we don't

### In scope for the prototype
- Decision API (`POST /v1/decision`)
- CAMARA signal collector with fallback handling
- AI risk engine: feature builder, scoring, fusion rules
- Explanation generator producing audit text
- Bank-side demo dashboard showing live decisions
- Customer profile store for behavioural baselines

### Deliberately out of scope
- Production card-network integration (ISO 8583 / VisaNet)
- Real customer PII — all profiles are synthetic
- Full regulatory certification and pen-testing
- Multi-operator commercial aggregation
- Model training on real historical fraud data

### Real vs simulated — answer this before being asked

| Component | Status in prototype | Path to production |
|---|---|---|
| CAMARA API calls | Sandbox / Network-as-Code | Swap base URL + credentials to MNO's live gateway |
| Bank fraud engine | Mock service we wrote | Replaced by the bank's real engine calling our endpoint |
| Cardholder profiles | Synthetic dataset | Bank supplies its own behavioural features |
| Risk scoring logic | Implemented and running | Retrained on the bank's labelled fraud history |
| Explanation output | Implemented and running | Mapped to the bank's audit and dispute format |

### Honest limitations
- No validation against real labelled fraud data
- Synthetic profiles cannot capture true behavioural variance
- Sandbox latency is not live-network latency
- Single-operator testing only

**The coverage question is the real one.** TravelGuard only helps a customer
whose operator exposes CAMARA. That makes operator adoption across MENA a
prerequisite for the product — and equally, a concrete commercial reason for
operators to adopt. Know which operators Nokia actually fronts in Morocco before
judges ask, because they will.

**Inbound roamers are the hard case.** Ahmed is a German subscriber in Morocco —
the signal must come from his *home* operator, resolved through the visited
network. That is a federation question, not an integration question, and it is
precisely why GSMA Open Gateway exists. Our headline scenario is the one most
dependent on federation working. Acknowledge it before someone else does.

---

## 9. Metrics to actually measure

Section 8 of the prototype PDF still has `[ your figure ]` placeholders. **These
must be filled with real numbers from a test run before submission** — judges
will trust a modest measured number far more than an impressive unmeasured one.

| Metric | Why it is the right measure |
|---|---|
| False-positive rate on genuine travellers | This is the entire problem statement — the metric the bank feels in its call centre |
| Detection rate on takeover cases | Reducing blocks is worthless if fraud starts getting through |
| End-to-end decision latency | A payment authorisation cannot wait; the budget is unforgiving |
| CAMARA calls per decision | Determines whether the unit economics work at scale |
| Decisions with a complete explanation | An unexplainable decision is not deployable in a regulated bank |

Instrument these in the API from the start — emit them as structured logs per
decision so the numbers are a query, not a scramble the night before.

---

## 10. Build order

1. **Freeze the feature-object contract** between orchestrator and risk engine.
   Everything else parallelises behind it.
2. FastAPI skeleton + pydantic request/response models + Swagger.
3. Mock CAMARA adapters with latency and failure simulation.
4. Orchestrator with cost-aware escalation and `asyncio.gather` + per-call timeouts.
5. Risk engine against mocks: features → fusion → score → decision → explanation.
6. Three demo scenarios green as automated tests.
7. Live Nokia sandbox behind the same adapter interface — config change only.
8. Frontend against the real endpoint.
9. Instrument metrics, run the measurement pass, fill the PDF placeholders.
10. Docker.

---

## 11. Vision — the one-liner

> TravelGuard AI is the decision intelligence layer that banks plug into their
> fraud engine — and CAMARA APIs are the trusted network signals it reasons over.

**Mission:** protect banks from fraud while ensuring legitimate travellers can
pay anywhere in the world, without unnecessary card blocks.

**Path to pilot:** shadow mode with one bank (score alongside the existing
engine, compare decisions, affect nothing) → retrain on real labelled data →
live pilot on a travel-heavy segment → second operator, second market → per-decision
commercial pricing shared between issuer and operator.

**What we would ask of an operator partner:** production CAMARA access in one
MENA market, realistic latency and availability figures, indicative per-call
commercial terms, and an introduction to one issuing bank for shadow mode.

**Note on positioning:** all four APIs work on **4G**. This is deployable across
MENA today, not waiting on 5G standalone rollout. That is a strength — say it
out loud rather than leaving it implicit. 5G adds finer location granularity,
standardised network exposure (NEF) that makes these APIs cheap for operators to
serve, and lower latency — but it is an improvement, not a prerequisite.
