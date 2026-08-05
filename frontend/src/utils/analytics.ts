import type { Decision } from "../types/api";
import type { DecisionRecord } from "../types/dashboard";

export function average(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function countByDecision(records: DecisionRecord[]) {
  return records.reduce<Record<Decision, number>>(
    (totals, record) => {
      totals[record.response.decision] += 1;
      return totals;
    },
    { APPROVE: 0, STEP_UP: 0, REJECT: 0 },
  );
}

export function dashboardMetrics(records: DecisionRecord[]) {
  const decisions = countByDecision(records);
  return {
    total: records.length,
    approved: decisions.APPROVE,
    stepUp: decisions.STEP_UP,
    rejected: decisions.REJECT,
    averageRisk: average(records.map((record) => record.response.risk_score)),
    averageLatency: average(records.map((record) => record.response.latency_ms)),
    camaraCalls: records.reduce((sum, record) => sum + record.response.camara_calls.length, 0),
  };
}

export function riskDistribution(records: DecisionRecord[]) {
  const buckets = [
    { range: "0-.2", count: 0 },
    { range: ".2-.4", count: 0 },
    { range: ".4-.6", count: 0 },
    { range: ".6-.8", count: 0 },
    { range: ".8-1", count: 0 },
  ];
  records.forEach((record) => {
    const index = Math.min(4, Math.floor(record.response.risk_score / 0.2));
    buckets[index].count += 1;
  });
  return buckets;
}

export function latencyHistogram(records: DecisionRecord[]) {
  const buckets = [
    { range: "0-25", count: 0 },
    { range: "25-40", count: 0 },
    { range: "40-55", count: 0 },
    { range: "55+", count: 0 },
  ];
  records.forEach((record) => {
    const latency = record.response.latency_ms;
    if (latency < 25) buckets[0].count += 1;
    else if (latency < 40) buckets[1].count += 1;
    else if (latency < 55) buckets[2].count += 1;
    else buckets[3].count += 1;
  });
  return buckets;
}

export function camaraUsage(records: DecisionRecord[]) {
  const counts = new Map<string, number>();
  records.forEach((record) => {
    record.response.camara_calls.forEach((api) => counts.set(api, (counts.get(api) || 0) + 1));
  });
  return Array.from(counts.entries())
    .map(([api, count]) => ({ api: api.replaceAll("_", " "), count }))
    .sort((a, b) => b.count - a.count);
}

export function decisionTrend(records: DecisionRecord[]) {
  return records
    .slice(0, 12)
    .reverse()
    .map((record, index) => ({
      label: `${index + 1}`,
      risk: Number(record.response.risk_score.toFixed(3)),
      latency: Number(record.response.latency_ms.toFixed(1)),
      decision: record.response.decision,
    }));
}

export function decisionPie(records: DecisionRecord[]) {
  const counts = countByDecision(records);
  return [
    { name: "Approved", value: counts.APPROVE, fill: "#34d399" },
    { name: "Step-up", value: counts.STEP_UP, fill: "#fbbf24" },
    { name: "Rejected", value: counts.REJECT, fill: "#fb7185" },
  ];
}
