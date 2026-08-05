import { BookOpen, ExternalLink, Server } from "lucide-react";

import { apiDocsUrl, openApiUrl } from "../services/api";

const exampleRequest = {
  transaction: {
    transaction_id: "tx-2026-0001",
    amount: 725.5,
    currency: "USD",
    merchant_country: "MA",
    timestamp: "2026-08-05T12:30:00Z",
    device_id: "device-123",
    ip_address: "203.0.113.10",
  },
  customer_profile: {
    customer_id: "cust-001",
    home_country: "US",
    trusted_devices: ["device-123"],
    last_sim_swap_days: 180,
    travel_frequency: 4,
    avg_transaction_amount: 110,
    phone_number: "+15555550123",
  },
  signals: {
    location: {
      provider: "bank-cache",
      confidence: 0.92,
      country: "MA",
      verified: true,
    },
  },
};

const exampleResponse = {
  decision: "STEP_UP",
  risk_score: 0.2625,
  confidence: 0.7375,
  explanation: ["medium_risk_score", "feature:trusted_device:1.000", "feature:location_verified:0.920"],
  signals_used: ["location", "roaming", "device_location", "sim_swap"],
  camara_calls: ["roaming", "device_location", "sim_swap"],
  latency_ms: 36.84,
  request_id: "demo-request-1",
};

export function ApiDocumentation() {
  return (
    <div className="space-y-6">
      <section className="grid gap-4 lg:grid-cols-3">
        <a
          href={apiDocsUrl()}
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border border-line bg-white p-5 shadow-card transition hover:border-blue-200 hover:bg-blue-50/30"
        >
          <BookOpen className="size-5 text-blue-700" />
          <h2 className="mt-4 text-lg font-semibold text-zinc-950">Swagger UI</h2>
          <p className="mt-2 text-sm text-zinc-500">Open the generated FastAPI documentation.</p>
          <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-blue-700">
            Open docs <ExternalLink className="size-4" />
          </span>
        </a>
        <a
          href={openApiUrl()}
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border border-line bg-white p-5 shadow-card transition hover:border-blue-200 hover:bg-blue-50/30"
        >
          <Server className="size-5 text-emerald-600" />
          <h2 className="mt-4 text-lg font-semibold text-zinc-950">OpenAPI JSON</h2>
          <p className="mt-2 text-sm text-zinc-500">Inspect the machine-readable service contract.</p>
          <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-emerald-700">
            View schema <ExternalLink className="size-4" />
          </span>
        </a>
        <div className="rounded-lg border border-line bg-white p-5 shadow-card">
          <h2 className="text-lg font-semibold text-zinc-950">Production endpoint</h2>
          <p className="mt-2 text-sm text-zinc-500">The dashboard reads API location from `VITE_API_BASE_URL`.</p>
          <code className="mt-4 block rounded-lg border border-line bg-zinc-50 p-3 text-sm font-medium text-zinc-700">POST /v1/decision</code>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-lg border border-line bg-white p-5 shadow-card">
          <h2 className="text-lg font-semibold text-zinc-950">Example request</h2>
          <pre className="mt-4 max-h-[520px] overflow-auto rounded-lg border border-line bg-zinc-50 p-4 text-sm text-zinc-700">
            {JSON.stringify(exampleRequest, null, 2)}
          </pre>
        </div>
        <div className="rounded-lg border border-line bg-white p-5 shadow-card">
          <h2 className="text-lg font-semibold text-zinc-950">Example response</h2>
          <pre className="mt-4 max-h-[520px] overflow-auto rounded-lg border border-line bg-zinc-50 p-4 text-sm text-zinc-700">
            {JSON.stringify(exampleResponse, null, 2)}
          </pre>
        </div>
      </section>
    </div>
  );
}
