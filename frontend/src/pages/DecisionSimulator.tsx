import { AlertCircle, CheckCircle2, Loader2, Network, Send, Smartphone, Wifi } from "lucide-react";
import { useMemo, useState } from "react";

import { DecisionBadge } from "../components/DecisionBadge";
import { DecisionTimeline } from "../components/DecisionTimeline";
import { RiskGauge } from "../components/RiskGauge";
import { useDecisionHistory } from "../hooks/useDecisionHistory";
import { useDecisionMutation } from "../hooks/useTravelGuardApi";
import { useToast } from "../hooks/useToast";
import type { DecisionRequest, DecisionResponse } from "../types/api";
import type { DecisionRecord } from "../types/dashboard";
import { formatLatency, formatPercent } from "../utils/format";

interface SimulatorForm {
  phoneNumber: string;
  amount: number;
  currency: string;
  merchantCountry: string;
  merchantName: string;
  deviceId: string;
}

const initialForm: SimulatorForm = {
  phoneNumber: "+15555550123",
  amount: 725.5,
  currency: "USD",
  merchantCountry: "MA",
  merchantName: "",
  deviceId: "device-123",
};

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-zinc-700">{label}</span>
      <div className="mt-2">{children}</div>
    </label>
  );
}

function inputClass() {
  return "h-11 w-full rounded-lg border border-line bg-white px-3 text-sm text-zinc-800 outline-none transition placeholder:text-zinc-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-50";
}

function Toggle({
  label,
  checked,
  onChange,
  icon: Icon,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  icon: typeof Wifi;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`flex items-center justify-between rounded-lg border p-3 text-left transition ${checked ? "border-blue-200 bg-blue-50 text-blue-700 font-medium" : "border-line bg-white text-zinc-500 hover:bg-zinc-50"
        }`}
    >
      <span className="inline-flex items-center gap-2 text-sm font-medium">
        <Icon className="size-4" />
        {label}
      </span>
      <span className={`size-2 rounded-full ${checked ? "bg-blue-600" : "bg-zinc-400"}`} />
    </button>
  );
}

function buildPayload(form: SimulatorForm): DecisionRequest {
  return {
    transaction: {
      transaction_id: `tx-sim-${Date.now()}`,
      amount: Number(form.amount),
      currency: form.currency,
      merchant_country: form.merchantCountry.toUpperCase(),
      merchant_name: form.merchantName.trim() || undefined,
      timestamp: new Date().toISOString(),
      device_id: form.deviceId.trim() || undefined,
      ip_address: "203.0.113.10",
    },
    customer_profile: {
      customer_id: "cust-001",
      home_country: "US",
      trusted_devices: form.deviceId.trim() ? [form.deviceId.trim()] : [],
      phone_number: form.phoneNumber,
    },
    signals: {},
  };
}

export function DecisionSimulator() {
  const [form, setForm] = useState<SimulatorForm>(initialForm);
  const [result, setResult] = useState<DecisionResponse | undefined>();
  const [lastPayload, setLastPayload] = useState<DecisionRequest | undefined>();
  const [lastRecord, setLastRecord] = useState<DecisionRecord | undefined>();
  const mutation = useDecisionMutation();
  const { addDecision } = useDecisionHistory();
  const { pushToast } = useToast();

  const payloadPreview = useMemo(() => buildPayload(form), [form]);

  const update = <K extends keyof SimulatorForm>(key: K, value: SimulatorForm[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const analyze = async () => {
    const payload = buildPayload(form);
    setLastPayload(payload);
    try {
      const response = await mutation.mutateAsync(payload);
      setResult(response);
      const record = addDecision(payload, response, "simulator");
      setLastRecord(record);
      pushToast({
        tone: "success",
        title: "Decision completed",
        description: `${response.decision.replace("_", "-")} returned in ${response.latency_ms.toFixed(1)} ms.`,
      });
    } catch (error) {
      pushToast({
        tone: "error",
        title: "Decision request failed",
        description: error instanceof Error ? error.message : "The backend could not score this transaction.",
      });
    }
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_0.85fr]">
      <section className="rounded-lg border border-line bg-white p-5 shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-zinc-950">Simulate a transaction</h2>
            <p className="text-sm text-zinc-500">Send a realistic bank transaction through the existing FastAPI decision service.</p>
          </div>
          <button
            type="button"
            onClick={analyze}
            disabled={mutation.isPending}
            className="inline-flex h-11 items-center justify-center gap-2 rounded-lg border border-blue-600 bg-blue-600 px-4 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mutation.isPending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Analyze Transaction
          </button>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <Field label="Phone Number">
            <input className={inputClass()} value={form.phoneNumber} onChange={(event) => update("phoneNumber", event.target.value)} />
          </Field>
          <Field label="Amount">
            <input className={inputClass()} type="number" min="1" value={form.amount} onChange={(event) => update("amount", Number(event.target.value))} />
          </Field>
          <Field label="Currency">
            <select className={inputClass()} value={form.currency} onChange={(event) => update("currency", event.target.value)}>
              <option>USD</option>
              <option>EUR</option>
              <option>GBP</option>
              <option>MAD</option>
              <option>AED</option>
            </select>
          </Field>
          <Field label="Merchant Country">
            <input className={inputClass()} value={form.merchantCountry} onChange={(event) => update("merchantCountry", event.target.value)} maxLength={2} />
          </Field>
          <Field label="Merchant Name">
            <input className={inputClass()} value={form.merchantName} onChange={(event) => update("merchantName", event.target.value)} placeholder="Optional" />
          </Field>
          <Field label="Device ID">
            <input className={inputClass()} value={form.deviceId} onChange={(event) => update("deviceId", event.target.value)} placeholder="Optional" />
          </Field>
        </div>

        <details className="mt-6 rounded-lg border border-line bg-zinc-50 p-4">
          <summary className="cursor-pointer text-sm font-medium text-zinc-700 outline-none">Request preview</summary>
          <pre className="mt-4 max-h-80 overflow-auto text-xs text-zinc-600">{JSON.stringify(payloadPreview, null, 2)}</pre>
        </details>
      </section>

      <aside className="space-y-4">
        {result ? (
          <section className="rounded-lg border border-line bg-white p-5 shadow-card">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm text-zinc-500">Decision result</p>
                <h2 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-950">{result.decision.replace("_", "-")}</h2>
              </div>
              <DecisionBadge decision={result.decision} large />
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-line bg-zinc-50 p-3">
                <p className="text-xs text-zinc-500">Risk Score</p>
                <p className="mt-1 text-lg font-semibold text-zinc-950">{formatPercent(result.risk_score)}</p>
              </div>
              <div className="rounded-lg border border-line bg-zinc-50 p-3">
                <p className="text-xs text-zinc-500">Confidence</p>
                <p className="mt-1 text-lg font-semibold text-zinc-950">{formatPercent(result.confidence)}</p>
              </div>
              <div className="rounded-lg border border-line bg-zinc-50 p-3">
                <p className="text-xs text-zinc-500">Latency</p>
                <p className="mt-1 text-lg font-semibold text-zinc-950">{formatLatency(result.latency_ms)}</p>
              </div>
              <div className="rounded-lg border border-line bg-zinc-50 p-3">
                <p className="text-xs text-zinc-500">Request ID</p>
                <p className="mt-1 truncate font-mono text-xs text-zinc-600">{result.request_id}</p>
              </div>
            </div>
            <div className="mt-4">
              <RiskGauge value={result.risk_score} />
            </div>
            <div className="mt-4 grid gap-3">
              <div className="rounded-lg border border-line bg-zinc-50 p-3">
                <h3 className="text-sm font-semibold text-zinc-950 mb-3">Network Signals Panel</h3>
                <div className="space-y-4">
                  {Object.entries(result.network_signals || {}).map(([key, value]: [string, any]) => (
                    <div key={key} className="flex flex-col gap-1 rounded-md border border-zinc-200 bg-white p-3 shadow-card">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize text-zinc-800 flex items-center gap-2">
                          <CheckCircle2 className="size-4 text-emerald-500" />
                          {key.replaceAll("_", " ")}
                        </span>
                        {value.api_latency_ms && <span className="text-xs text-zinc-500">{value.api_latency_ms}ms</span>}
                      </div>
                      {typeof value === 'object' && (
                        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-600">
                          {value.confidence && (
                            <div className="flex items-center gap-1">
                              <span className="font-medium text-zinc-500">Confidence:</span> {formatPercent(value.confidence)}
                            </div>
                          )}
                          {value.provider && (
                            <div className="flex items-center gap-1">
                              <span className="font-medium text-zinc-500">Provider:</span> {value.provider}
                            </div>
                          )}
                          {value.country && (
                            <div className="flex items-center gap-1">
                              <span className="font-medium text-zinc-500">Country:</span> {value.country}
                            </div>
                          )}
                          {value.roaming !== undefined && (
                            <div className="flex items-center gap-1">
                              <span className="font-medium text-zinc-500">Roaming:</span> {value.roaming ? 'Yes' : 'No'}
                            </div>
                          )}
                          {value.days_since_swap !== undefined && (
                            <div className="flex items-center gap-1">
                              <span className="font-medium text-zinc-500">Days Since Swap:</span> {value.days_since_swap}
                            </div>
                          )}
                          {value.verified !== undefined && (
                            <div className="flex items-center gap-1">
                              <span className="font-medium text-zinc-500">Verified:</span> {value.verified ? 'Yes' : 'No'}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="mt-4 pt-4 border-t border-line">
                  <TokenList title="APIs Called" items={result.camara_calls} />
                </div>
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-zinc-950">Explainability</h3>
              <div className="mt-3 space-y-2">
                {result.explanation.map((item) => (
                  <div key={item} className="rounded-lg border border-line bg-zinc-50 px-3 py-2 text-sm text-zinc-700">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </section>
        ) : (
          <section className="rounded-lg border border-line bg-white p-5 shadow-card">
            <h2 className="text-lg font-semibold text-zinc-950">Result panel</h2>
            <p className="mt-2 text-sm text-zinc-500">Analyze a transaction to view risk, confidence, provider signals, and explanations.</p>
          </section>
        )}
        <DecisionTimeline record={lastRecord || (lastPayload && result ? { id: "preview", createdAt: new Date().toISOString(), request: lastPayload, response: result, source: "simulator" } : undefined)} />
      </aside>
    </div>
  );
}

function TokenList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-line bg-zinc-50 p-3">
      <h3 className="text-sm font-semibold text-zinc-950">{title}</h3>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.length ? (
          items.map((item) => (
            <span key={item} className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs font-medium text-zinc-600 shadow-card">
              {item.replaceAll("_", " ")}
            </span>
          ))
        ) : (
          <span className="text-sm text-zinc-500">None</span>
        )}
      </div>
    </div>
  );
}
