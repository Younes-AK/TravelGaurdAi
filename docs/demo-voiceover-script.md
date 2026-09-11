# TravelGuard AI — 60-Second Demo Voiceover Script

Matches `travelguard-ai-demo.gif` (screen recording of the live app: Dashboard → Decision Simulator → Decision History → System Status → Dashboard).

Read at a normal, confident pace. Total ≈ 60 seconds (~150 words).

---

**[0:00–0:08] — Dashboard**

> "This is TravelGuard AI — a decision layer banks call before blocking a
> cross-border card transaction. Right now it's processed 18 decisions:
> approvals, step-ups, and rejections, with full visibility into risk
> scores, latency, and every network signal the engine used to decide."

**[0:08–0:14] — Decision Simulator**

> "Here's the simulator. We send a realistic bank transaction straight
> into our FastAPI decision service — no mocks in the UI, this is the real
> pipeline."

**[0:14–0:26] — Run the "Fraud" scenario**

> "Let's try a suspicious case: a SIM swapped hours ago, followed by a
> large money transfer. The engine calls the CAMARA network APIs —
> roaming, SIM swap, device location, number verification — fuses them
> into a risk score, and comes back in under 70 milliseconds with a
> decision and a full explanation, not just a number."

**[0:26–0:36] — Decision History**

> "Every decision is logged here — amount, country, risk score, latency —
> so a bank can audit exactly why a transaction was approved, escalated,
> or blocked."

**[0:36–0:46] — System Status**

> "And this is the operational view: backend health, provider status, and
> which risk model is live — everything a bank's ops team needs before
> trusting this in production."

**[0:46–0:60] — Back to Dashboard / closing**

> "TravelGuard AI turns network signals banks already have access to into
> real-time, explainable fraud decisions — protecting revenue without
> blocking legitimate travelers. Thank you."

---

### Notes for recording your voiceover
- The clip currently shows all three canned demo scenarios trending toward
  `STEP-UP` rather than their labeled Approve/Step-up/Reject outcomes —
  that's why the script says "a decision and a full explanation" rather
  than naming a specific verdict like "rejected." If you fix the risk
  engine thresholds before submission, you can tighten that line to name
  the actual outcome (e.g., "...and rejects it in under 70ms").
- Timestamps are approximate — nudge speech pacing, not the GIF, since the
  recording is fixed.
