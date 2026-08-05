import type { Decision } from "../types/api";

export const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export const numberFormatter = new Intl.NumberFormat("en-US");

export function formatAmount(amount: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: amount >= 1000 ? 0 : 2,
  }).format(amount);
}

export function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function formatLatency(value: number) {
  return `${value.toFixed(value >= 100 ? 0 : 1)} ms`;
}

export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function decisionTone(decision: Decision) {
  if (decision === "APPROVE") {
    return {
      label: "Approved",
      dot: "bg-emerald-500",
      badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
      text: "text-emerald-800",
      chart: "#10b981",
    };
  }
  if (decision === "STEP_UP") {
    return {
      label: "Step-up",
      dot: "bg-orange-500",
      badge: "border-orange-200 bg-orange-50 text-orange-700",
      text: "text-orange-800",
      chart: "#f97316",
    };
  }
  return {
    label: "Rejected",
    dot: "bg-rose-500",
    badge: "border-rose-200 bg-rose-50 text-rose-700",
    text: "text-rose-800",
    chart: "#ef4444",
  };
}

export function compactId(id: string) {
  if (id.length <= 12) return id;
  return `${id.slice(0, 6)}...${id.slice(-4)}`;
}
