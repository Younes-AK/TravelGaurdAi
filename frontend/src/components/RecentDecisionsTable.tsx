import { ArrowDownUp, Search } from "lucide-react";
import { useMemo, useState } from "react";

import type { Decision } from "../types/api";
import type { DecisionRecord } from "../types/dashboard";
import { compactId, formatAmount, formatDateTime, formatLatency, formatPercent } from "../utils/format";
import { DecisionBadge } from "./DecisionBadge";
import { EmptyState } from "./EmptyState";

type SortKey = "timestamp" | "amount" | "risk" | "latency";

export function RecentDecisionsTable({
  records,
  onSelect,
}: {
  records: DecisionRecord[];
  onSelect?: (record: DecisionRecord) => void;
}) {
  const [query, setQuery] = useState("");
  const [decision, setDecision] = useState<Decision | "ALL">("ALL");
  const [sortKey, setSortKey] = useState<SortKey>("timestamp");

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return records
      .filter((record) => {
        if (decision !== "ALL" && record.response.decision !== decision) return false;
        if (!normalized) return true;
        return [
          record.response.request_id,
          record.request.transaction.transaction_id,
          record.request.transaction.merchant_country,
          record.request.customer_profile.customer_id,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalized);
      })
      .sort((a, b) => {
        if (sortKey === "amount") return b.request.transaction.amount - a.request.transaction.amount;
        if (sortKey === "risk") return b.response.risk_score - a.response.risk_score;
        if (sortKey === "latency") return b.response.latency_ms - a.response.latency_ms;
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      });
  }, [decision, query, records, sortKey]);

  return (
    <div className="rounded-lg border border-line bg-white shadow-card">
      <div className="flex flex-col gap-3 border-b border-line p-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-zinc-950">Recent decisions</h2>
          <p className="text-sm text-zinc-500">Search, filter, and sort the active analyst session.</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <label className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-zinc-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="h-10 w-full rounded-lg border border-line bg-white pl-9 pr-3 text-sm text-zinc-800 outline-none transition placeholder:text-zinc-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-50 sm:w-64"
              placeholder="Search request, country, customer"
            />
          </label>
          <select
            value={decision}
            onChange={(event) => setDecision(event.target.value as Decision | "ALL")}
            className="h-10 rounded-lg border border-line bg-white px-3 text-sm text-zinc-800 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
          >
            <option value="ALL">All decisions</option>
            <option value="APPROVE">Approved</option>
            <option value="STEP_UP">Step-up</option>
            <option value="REJECT">Rejected</option>
          </select>
          <button
            type="button"
            onClick={() => setSortKey(sortKey === "timestamp" ? "risk" : sortKey === "risk" ? "latency" : "timestamp")}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-line bg-white px-3 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50"
          >
            <ArrowDownUp className="size-4" />
            Sort: {sortKey}
          </button>
        </div>
      </div>
      {filtered.length ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase tracking-[0.12em] text-zinc-500">
              <tr className="border-b border-line">
                <th className="px-4 py-3 font-medium">Request ID</th>
                <th className="px-4 py-3 font-medium">Amount</th>
                <th className="px-4 py-3 font-medium">Country</th>
                <th className="px-4 py-3 font-medium">Decision</th>
                <th className="px-4 py-3 font-medium">Risk Score</th>
                <th className="px-4 py-3 font-medium">Confidence</th>
                <th className="px-4 py-3 font-medium">Latency</th>
                <th className="px-4 py-3 font-medium">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((record) => (
                <tr
                  key={record.id}
                  onClick={() => onSelect?.(record)}
                  className="cursor-pointer border-b border-line/70 transition hover:bg-blue-50/40"
                >
                  <td className="px-4 py-3 font-mono text-xs text-zinc-600">{compactId(record.response.request_id)}</td>
                  <td className="px-4 py-3 font-semibold text-zinc-900">
                    {formatAmount(record.request.transaction.amount, record.request.transaction.currency)}
                  </td>
                  <td className="px-4 py-3 text-zinc-750">{record.request.transaction.merchant_country}</td>
                  <td className="px-4 py-3">
                    <DecisionBadge decision={record.response.decision} />
                  </td>
                  <td className="px-4 py-3 text-zinc-800 font-medium">{formatPercent(record.response.risk_score)}</td>
                  <td className="px-4 py-3 text-zinc-700">{formatPercent(record.response.confidence)}</td>
                  <td className="px-4 py-3 text-zinc-700">{formatLatency(record.response.latency_ms)}</td>
                  <td className="px-4 py-3 text-zinc-500">{formatDateTime(record.createdAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="p-4">
          <EmptyState
            icon={Search}
            title="No matching decisions"
            description="Adjust the search or decision filter to review a broader set of transactions."
          />
        </div>
      )}
    </div>
  );
}
