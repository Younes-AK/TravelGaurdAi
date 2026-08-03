# Network APIs — Integration Reference

How TravelGuard AI consumes GSMA Open Gateway CAMARA APIs via the Nokia
Network-as-Code platform, and what 4G/5G actually exposes underneath.

Written against CAMARA specs as of August 2026 and `network_as_code` Python SDK v10.0.0.

---

## 1. The three layers, and how they relate

These are not three alternatives. They stack:

```
4G/5G network capabilities     what the network physically knows
        │                       (HSS/UDM, AMF, MME, VLR, roaming signalling)
        ▼
CAMARA APIs                    the standard REST contract over those capabilities
        │                       (Linux Foundation; the spec, not an endpoint)
        ▼
GSMA Open Gateway              the federation — one contract, many operators
        │
        ▼
Nokia Network-as-Code          the aggregator we actually call: one key, one
                               base URL, routes to the right operator gateway
```

**Practical consequence for us:** we write against the CAMARA schema, we call
Nokia's host. If we later move to Orange Morocco's own gateway or Telefónica's,
the request and response bodies are identical — only the base URL and credentials
change. This is exactly the "adapter interface" the prototype doc promises, and
it is genuinely true, not marketing.

---

## 2. The four APIs we use

### 2.1 Device Roaming Status

Repo: [`camaraproject/DeviceRoamingStatus`](https://github.com/camaraproject/DeviceRoamingStatus)
(split out of the older `DeviceStatus` repo; Nokia still exposes it under a
`device_status` namespace).

```
POST {apiRoot}/device-roaming-status/v1/retrieve
Scope: device-roaming-status:read
```

Request:
```json
{ "device": { "phoneNumber": "+4915112345678" } }
```
`device` accepts `phoneNumber`, `ipv4Address`, `ipv6Address`, or
`networkAccessIdentifier`. Any given MNO may support only a subset — send
`phoneNumber` for our use case. `device` is omitted entirely when using a
three-legged token (the token identifies the subscriber).

Response:
```json
{
  "roaming": true,
  "countryCode": 604,
  "countryName": ["MA"],
  "lastStatusTime": "2026-08-03T09:14:22Z"
}
```

| Field | Type | Notes |
|---|---|---|
| `roaming` | boolean, **required** | true if roaming |
| `countryCode` | integer 100–999 | MCC. Morocco = 604, Germany = 262, Turkey = 286 |
| `countryName` | string[] | ISO 3166 alpha-2 mapped from MCC. **Empty array if no mapping** — an MCC can map to several countries or none |
| `lastStatusTime` | RFC 3339 + timezone, **required** | This is the freshness signal. Feed it into the feature vector — roaming confirmed 4 hours ago ≠ confirmed 6 days ago |

**Watch out:** `countryName` is an *array*, and it can be empty even on a
successful call. Code that does `resp["countryName"][0]` will crash in
production on some MCCs. Normalise to `Optional[str]` in the adapter.

### 2.2 SIM Swap

Repo: [`camaraproject/SimSwap`](https://github.com/camaraproject/SimSwap)

```
POST {apiRoot}/sim-swap/v2/check          → boolean
POST {apiRoot}/sim-swap/v2/retrieve-date  → timestamp
POST {apiRoot}/sim-swap/v2/retrieve-age-band  → coarse band (may return 501)
Scopes: sim-swap:check | sim-swap:retrieve-date | sim-swap
```

`/check` request:
```json
{ "phoneNumber": "+4915112345678", "maxAge": 240 }
```
`maxAge` is **hours**, min 1, max 2400 (100 days), default 240.

`/check` response: `{ "swapped": false }`

`/retrieve-date` response:
```json
{ "latestSimChange": "2025-12-01T08:00:00Z", "monitoredPeriod": 365 }
```

**Which one to call:** our fusion rules need *days since SIM change* as a
continuous feature, not a boolean — "swapped 1 day ago" and "swapped 200 days
ago" mean opposite things. So call **`/retrieve-date`**, not `/check`.
`/check` is only adequate if the bank has a fixed policy window.

`/retrieve-age-band` is the privacy-preserving variant (bands 1–17, plus the
sentinel `111` = never swapped). Some operators return **501 NOT_IMPLEMENTED**
for it. Treat it as a fallback, not a primary.

### 2.3 Device Location Verification

Repo: [`camaraproject/DeviceLocation`](https://github.com/camaraproject/DeviceLocation)

```
POST {apiRoot}/location-verification/v3/verify
Scope: location-verification:verify
```

Request:
```json
{
  "device": { "phoneNumber": "+4915112345678" },
  "area": {
    "areaType": "CIRCLE",
    "center": { "latitude": 31.6295, "longitude": -7.9811 },
    "radius": 50000
  },
  "maxAge": 3600
}
```
`radius` is in **metres**, minimum 1. `maxAge` here is in **seconds** — note the
unit differs from SimSwap's hours. Absent `maxAge` means "any age accepted".

Response:
```json
{
  "verificationResult": "TRUE",
  "lastLocationTime": "2026-08-03T09:12:00Z",
  "matchRate": 87
}
```

`verificationResult` is `TRUE` | `FALSE` | **`PARTIAL`**. `matchRate` (1–99) is
present *only* when the result is `PARTIAL`.

**This is the important subtlety for our risk engine.** This API is
*verification*, not retrieval — you ask "is the device inside this circle?" and
get a yes/no/partial. `PARTIAL` means the network's uncertainty region overlaps
your circle. Mapping `PARTIAL` to `FALSE` would manufacture false positives,
which is the exact failure mode the whole product exists to fix. Map it to a
graded feature: `matchRate/100`, and let the fusion layer weigh it.

Errors worth handling explicitly (all HTTP 422):
- `LOCATION_VERIFICATION.UNABLE_TO_LOCATE` — network can't locate the device
- `LOCATION_VERIFICATION.AREA_NOT_COVERED` — the requested area isn't served
- `LOCATION_VERIFICATION.UNABLE_TO_FULFILL_MAX_AGE` — no location fresh enough
- `LOCATION_VERIFICATION.INVALID_AREA` — circle below the minimum size

All four are *"we don't know"*, not *"the customer is lying"*. Per the prototype
doc's degradation strategy, these widen the confidence interval and push toward
step-up — they must never push toward reject.

There is also `POST /location-retrieval/.../retrieve` which returns an actual
area rather than a boolean. Heavier on consent and usually pricier. We don't
need it: we already know the merchant's country, so verification is the right
shape of question.

### 2.4 Number Verification

Repo: [`camaraproject/NumberVerification`](https://github.com/camaraproject/NumberVerification)

```
POST {apiRoot}/number-verification/v2/verify      → { "devicePhoneNumberVerified": bool }
GET  {apiRoot}/number-verification/v2/device-phone-number → { "devicePhoneNumber": "+..." }
Scopes: number-verification:verify | number-verification:device-phone-number:read
```

Request accepts either `phoneNumber` (plain E.164) or `hashedPhoneNumber`
(SHA-256 hex, `^[a-fA-F0-9]{64}$`). Exactly one — not both.

**This one is architecturally different from the other three, and it matters.**

Number Verification *requires* a three-legged token obtained through mobile-network
authentication — authorization code flow or CIBA. Not SMS OTP, not
username/password. The tokens are single-use, no refresh, max 5-minute lifetime.
It also implies the **device must be on mobile data**, because the operator
identifies the subscriber from the data session.

The consequence: it cannot be called synchronously from a card-authorisation
path the way the other three can. There is no user device in the loop at the
moment Ahmed's card is tapped at a café till.

So the orchestrator's step 4 ("if identity itself is in question → Number
Verification") is really a **step-up channel**, not a fourth inline signal: the
bank pushes to its mobile app, the app completes network auth, and the result
feeds back as an input to the decision. That is consistent with what the
prototype doc says on p.7 ("a push confirmation is sent, and the answer feeds
back into the decision") — but the demo dashboard should not imply it happens
inline in 400ms. Worth being precise about this in front of judges; it's the
kind of detail an operator on the panel will catch.

---

## 3. Auth: two-legged vs three-legged

| | Two-legged (client credentials) | Three-legged (auth code / CIBA) |
|---|---|---|
| Who is identified | the app | the app **and** the subscriber |
| Subscriber identified by | explicit `phoneNumber` in body | the token itself |
| Usable for | Roaming Status, SIM Swap, Location Verification | required for Number Verification |
| Consent | handled by operator/aggregator contract | captured per-user, in-flow |

Two rules that will bite:
- With a three-legged token, sending `device`/`phoneNumber` in the body is an
  **error**: `422 UNNECESSARY_IDENTIFIER`.
- With a two-legged token, omitting it is `422 MISSING_IDENTIFIER`.

CAMARA supports **CIBA in poll mode only** — the client polls the auth server
until the user authenticates. There is also a JWT Bearer flow, which is
synchronous and simpler when consent is already captured out of band; that is
the realistic path for a bank that captured consent at card issuance.

Ref: [CAMARA API access and user consent](https://github.com/camaraproject/IdentityAndConsentManagement/blob/main/documentation/CAMARA-API-access-and-user-consent.md)

---

## 4. Nokia Network-as-Code — concrete usage

### Access model

Nokia ships NaC through **RapidAPI**. The SDK's default environment is:

```python
class NetworkAsCodeApiEnvironment(enum.Enum):
    DEFAULT = "https://network-as-code.p-eu.rapidapi.com"
```

So: sign up on the Nokia NaC developer portal, subscribe to the API on RapidAPI,
get a RapidAPI key. That single key is the credential — the SDK sends it as the
RapidAPI auth header, and Nokia handles the operator-side OAuth behind it. That
is the whole reason to use an aggregator.

### Install

```bash
pip install network_as_code    # v10.0.0, requires Python >= 3.11
```
Depends on `httpx` and `pydantic v2` — same stack as our FastAPI service, so no
dependency conflict.

### Client

```python
import os
from network_as_code import NetworkAsCodeApi

client = NetworkAsCodeApi(
    rapidapi_host="network-as-code.nokia.rapidapi.com",
    api_key=os.environ["NAC_API_KEY"],
)
```

There is also an `environment=NetworkAsCodeApiEnvironment.DEFAULT` form in the
generated reference. The generated docs are inconsistent about the import
casing (`networkAsCode` vs `network_as_code`) — **`network_as_code` is the real
package name**, per `pyproject.toml`. Trust the package, not the reference file.

### The four calls

```python
from network_as_code.device_status import RetrieveRoamingStatusDeviceStatusRequestDevice
from network_as_code.location import VerifyLocationRequestDevice, VerifyLocationRequestArea

# 1. Roaming — always called
roaming = client.device_status.retrieve_roaming_status(
    device=RetrieveRoamingStatusDeviceStatusRequestDevice(phone_number="+99999991000"),
)

# 2. SIM swap — days-since, not boolean
sim = client.sim_swap.retrieve_date(phone_number="+99999991000")
# or the boolean form:
swapped = client.sim_swap.check(phone_number="+99999991000", max_age=240)

# 3. Location verification — only when signals disagree or amount is high
loc = client.location.verify(
    device=VerifyLocationRequestDevice(phone_number="+99999991000"),
    area=VerifyLocationRequestArea(
        area_type="CIRCLE",
        center={"latitude": 31.6295, "longitude": -7.9811},
        radius=50000,
    ),
    max_age=3600,
)

# 4. Number verification — three-legged, step-up channel only
verified = client.number_verification.verify(phone_number="+99999991000")
```

Every method also takes `correlator` (a correlation id propagated across
services) and `request_options`. **Set `correlator` to our `transaction_id`** —
it is free tracing across the whole decision, and it is what we show a judge who
asks "how would you debug this in production?".

### Sandbox

Simulated devices are keyed by phone number: `+99999991000` and neighbours.
Different test numbers are pre-configured to return different results —
including error responses. You get deterministic fixtures by swapping the
identifier, which is exactly what our three demo scenarios need. Confirm the
full number→behaviour table on the portal before demo day and pin it in
`backend/app/camara/sandbox_numbers.py`.

### Other namespaces present in the SDK

`qod`, `slice`, `geofencing`, `congestion_insights`, `device_swap`, `kyc`,
`number_recycling`, `call_forwarding_signal`, `consent_info`.

Two are worth knowing about for the pitch:
- **`kyc`** — KYC Match. Checks bank-held identity attributes (name, address,
  date of birth) against operator records without exposing either side's data.
  For an anti-fraud product pitched at a bank, this is the most obvious
  extension after v1, and it is a good answer to "what's next".
- **`device_swap`** — device change, distinct from SIM change. Same fraud
  signal family; a swapped handset with an unchanged SIM is its own pattern.

---

## 5. What "4G/5G network capabilities" actually means here

CAMARA has 20+ specs; only **Number Verification** and **SIM Swap** have reached
General Availability, which is why they are the most widely deployed. The
capabilities split into two families:

**Informational — reading network state.** This is our family. The signals come
from subscriber-management and mobility functions that have existed since 4G:
the HSS/UDM knows which IMSI is bound to which MSISDN and when that binding
changed (SIM swap); roaming signalling and the serving MME/AMF know the visited
network and country (roaming status); and cell-level attachment gives a coarse
location the operator can verify a claim against, without GPS and without the
handset cooperating.

That last point is the technical core of the whole pitch, so state it precisely:
**the location signal is attested by the network, not reported by the device.**
An app-reported GPS coordinate is a claim made by software running on hardware
the attacker may control. Network-side location is inferred from which radio the
SIM is actually attached to. That is what makes it hard to spoof, and it is why
the bank's existing IP/GPS/travel-notice proxies fail by construction.

**Programmatic — changing network behaviour.** Quality on Demand (stable latency
or throughput on request — the first CAMARA API standardised), Network Slicing,
edge/MEC discovery. Much more powerful in 5G standalone. Not relevant to
TravelGuard, but it is the reason 5G made this whole API category commercially
interesting, and worth one sentence if a judge asks why now.

**What 5G adds specifically:** finer location granularity, standardised network
exposure (NEF) making these APIs cheap for the operator to serve rather than
bespoke integrations, and lower-latency responses. Our four APIs work on 4G —
this is a deployable product today, not one waiting on 5G SA rollout across
MENA. That is a strength, and it should be said out loud rather than left
implicit.

---

## 6. Practical notes for our implementation

**Unit inconsistency.** SimSwap `maxAge` is hours; Location `maxAge` is seconds.
Normalise at the adapter boundary and never let raw units reach the risk engine.

**Version pinning.** Several CAMARA specs on `main` are marked `vwip` (work in
progress). Pin to the released version paths (`v1`, `v2`, `v3`) from the repo
Releases, not to `main` — the WIP schemas change under you.

**Coverage is the real risk, not latency.** The prototype doc already says this
and it is the honest framing. TravelGuard only helps a customer whose operator
exposes CAMARA. In practice the aggregator's operator footprint in MENA is the
binding constraint on the product — not our code. Know which operators Nokia
actually fronts in Morocco before the judges ask, because they will.

**Inbound roamers are the hard case.** Ahmed is a German subscriber in Morocco.
The signal has to come from *his home operator* (Deutsche Telekom / Vodafone DE),
resolved through the visited network. That is a federation question, not an
integration question, and it is precisely why GSMA Open Gateway exists rather
than everyone integrating operators one at a time. Our headline scenario is the
one that most depends on federation working — worth acknowledging before someone
else points it out.

---

## Sources

- [CAMARA DeviceRoamingStatus](https://github.com/camaraproject/DeviceRoamingStatus) · [SimSwap](https://github.com/camaraproject/SimSwap) · [DeviceLocation](https://github.com/camaraproject/DeviceLocation) · [NumberVerification](https://github.com/camaraproject/NumberVerification)
- [CAMARA Identity & Consent Management](https://github.com/camaraproject/IdentityAndConsentManagement/blob/main/documentation/CAMARA-API-access-and-user-consent.md)
- [Nokia Network-as-Code SDKs](https://github.com/nokia/network-as-code-sdks) · [developer portal](https://developer.networkascode.nokia.io/docs)
- [GSMA Open Gateway](https://www.gsma.com/solutions-and-impact/gsma-open-gateway/) · [API Sandbox](https://open-gateway.gsma.com/sandbox)
