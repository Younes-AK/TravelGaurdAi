import type { Decision, DecisionRequest, DecisionResponse } from "../types/api";
import type { DecisionRecord } from "../types/dashboard";

const countries = ["US", "MA", "FR", "GB", "ES", "AE", "SG", "DE", "CA", "JP"];
const currencies = ["USD", "EUR", "GBP", "MAD", "AED"];
const phones = ["+15555550123", "+212600000001", "+447700900123", "+971501234567"];

function pick<T>(items: T[]) {
  return items[Math.floor(Math.random() * items.length)];
}

function randomAmount() {
  const base = [42, 89, 132, 249, 520, 875, 1440, 2800, 5200];
  return Math.round((pick(base) + Math.random() * 180) * 100) / 100;
}

export function createRandomDecisionRequest(source = "live"): DecisionRequest {
  const deviceId = `device-${Math.floor(100 + Math.random() * 900)}`;
  const trusted = Math.random() > 0.35;
  const homeCountry = pick(["US", "GB", "FR", "DE", "CA"]);
  const merchantCountry = Math.random() > 0.55 ? homeCountry : pick(countries);
  const amount = randomAmount();

  return {
    transaction: {
      transaction_id: `tx-${source}-${Date.now()}-${Math.floor(Math.random() * 9999)}`,
      amount,
      currency: pick(currencies),
      merchant_country: merchantCountry,
      timestamp: new Date().toISOString(),
      device_id: deviceId,
      ip_address: `203.0.113.${Math.floor(10 + Math.random() * 180)}`,
    },
    customer_profile: {
      customer_id: `cust-${Math.floor(10000 + Math.random() * 90000)}`,
      home_country: homeCountry,
      trusted_devices: trusted ? [deviceId] : [],
      last_sim_swap_days: Math.floor(Math.random() * 420),
      travel_frequency: Math.floor(Math.random() * 18),
      avg_transaction_amount: Math.round((80 + Math.random() * 850) * 100) / 100,
      phone_number: pick(phones),
    },
    signals: Math.random() > 0.4 ? createSignalSet(homeCountry, merchantCountry) : {},
  };
}

export function createSignalSet(homeCountry: string, merchantCountry: string) {
  return {
    location: {
      provider: "bank-cache",
      confidence: Number((0.72 + Math.random() * 0.25).toFixed(2)),
      country: Math.random() > 0.5 ? merchantCountry : homeCountry,
      verified: true,
    },
    roaming:
      Math.random() > 0.45
        ? {
            provider: "bank-cache",
            confidence: Number((0.78 + Math.random() * 0.2).toFixed(2)),
            country: merchantCountry,
            roaming: merchantCountry !== homeCountry,
          }
        : undefined,
  };
}

function seedResponse(decision: Decision, score: number, latency: number, calls: string[]): DecisionResponse {
  const confidence = Math.max(score, 1 - score);
  return {
    decision,
    risk_score: score,
    confidence,
    explanation:
      decision === "APPROVE"
        ? ["trusted_device_and_low_risk", "feature:trusted_device:1.000", "feature:location_verified:0.940"]
        : decision === "STEP_UP"
          ? ["medium_risk_score", "feature:amount_ratio_to_average:4.218", "feature:roaming:1.000"]
          : ["high_risk_score", "recent_sim_swap", "feature:sim_swap_days:1.000"],
    signals_used: ["location", "roaming", ...calls].filter((value, index, arr) => arr.indexOf(value) === index),
    camara_calls: calls,
    latency_ms: latency,
    request_id: crypto.randomUUID(),
  };
}

export function seedDecisionHistory(): DecisionRecord[] {
  const specs: Array<[Decision, number, number, string[]]> = [
    ["APPROVE", 0.08, 28.4, ["roaming"]],
    ["STEP_UP", 0.43, 41.7, ["location", "device_location"]],
    ["REJECT", 0.91, 35.2, ["sim_swap", "number_verification"]],
    ["APPROVE", 0.17, 24.1, ["device_location"]],
    ["STEP_UP", 0.58, 49.9, ["roaming", "sim_swap"]],
    ["APPROVE", 0.22, 31.6, ["location"]],
    ["REJECT", 0.78, 44.8, ["location", "sim_swap"]],
    ["APPROVE", 0.11, 27.7, ["roaming"]],
    ["STEP_UP", 0.36, 39.4, ["number_verification"]],
    ["APPROVE", 0.19, 26.2, ["device_location"]],
    ["STEP_UP", 0.66, 53.3, ["location", "roaming", "sim_swap"]],
    ["APPROVE", 0.06, 22.9, ["location"]],
  ];

  return specs.map(([decision, score, latency, calls], index) => {
    const request = createRandomDecisionRequest(`seed-${index}`);
    const createdAt = new Date(Date.now() - index * 14 * 60 * 1000).toISOString();
    request.transaction.timestamp = createdAt;
    return {
      id: crypto.randomUUID(),
      createdAt,
      request,
      response: seedResponse(decision, score, latency, calls),
      source: "seed",
    };
  });
}
