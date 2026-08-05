import { Check, Cpu, FileInput, Network, ShieldCheck, Wand2, Zap } from "lucide-react";

import type { DecisionRecord, TimelineStep } from "../types/dashboard";
import { DecisionBadge } from "./DecisionBadge";

const icons = [FileInput, Network, Wand2, Cpu, ShieldCheck, Zap];

export function buildTimeline(record?: DecisionRecord): TimelineStep[] {
  return [
    {
      id: "received",
      title: "Transaction received",
      description: record
        ? `${record.request.transaction.currency} ${record.request.transaction.amount.toLocaleString()} in ${record.request.transaction.merchant_country}`
        : "Awaiting transaction payload",
      status: record ? "complete" : "pending",
      meta: record?.request.transaction.transaction_id,
    },
    {
      id: "camara",
      title: "CAMARA APIs",
      description: record?.response.camara_calls.length
        ? record.response.camara_calls.map((api) => api.replaceAll("_", " ")).join(", ")
        : "No additional provider call required",
      status: record ? "complete" : "pending",
    },
    {
      id: "features",
      title: "Feature Builder",
      description: "Transaction, profile, and signals converted into model features",
      status: record ? "complete" : "pending",
    },
    {
      id: "risk",
      title: "Risk Engine",
      description: record ? `Risk score ${record.response.risk_score.toFixed(3)}` : "Waiting for model score",
      status: record ? "complete" : "pending",
    },
    {
      id: "decision",
      title: "Decision",
      description: record ? "Policy rules and explainability returned a bank action" : "Decision not available",
      status: record ? "complete" : "pending",
    },
    {
      id: "response",
      title: "HTTP response",
      description: record ? `${record.response.latency_ms.toFixed(1)} ms total inference latency` : "Response pending",
      status: record ? "complete" : "pending",
      meta: record?.response.request_id,
    },
  ];
}

export function DecisionTimeline({ record }: { record?: DecisionRecord }) {
  const steps = buildTimeline(record);

  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">Decision timeline</h2>
          <p className="text-sm text-zinc-500">A bank request moving through the TravelGuard AI pipeline.</p>
        </div>
        {record ? <DecisionBadge decision={record.response.decision} large /> : null}
      </div>
      <div className="mt-6 space-y-4">
        {steps.map((step, index) => {
          const Icon = icons[index] || Check;
          return (
            <div
              key={step.id}
              className="grid grid-cols-[32px_1fr] gap-4"
            >
              <div className="relative">
                <div className="flex size-8 items-center justify-center rounded-lg border border-blue-100 bg-blue-50 text-blue-700">
                  <Icon className="size-4" />
                </div>
                {index < steps.length - 1 ? <div className="mx-auto mt-2 h-8 w-px bg-zinc-200" /> : null}
              </div>
              <div className="rounded-lg border border-line bg-zinc-50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-zinc-900">{step.title}</h3>
                  {step.meta ? <span className="text-xs text-zinc-500">{step.meta}</span> : null}
                </div>
                <p className="mt-1 text-sm text-zinc-600">{step.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
