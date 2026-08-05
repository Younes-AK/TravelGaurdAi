import { Activity, Gauge, Network, ShieldCheck, Timer, TriangleAlert, Zap } from "lucide-react";

import {
  CamaraUsageChart,
  DecisionPieChart,
  DecisionTrendChart,
  LatencyHistogramChart,
  RiskDistributionChart,
} from "../components/Charts";
import { KpiCard } from "../components/KpiCard";
import { RecentDecisionsTable } from "../components/RecentDecisionsTable";
import { useDecisionHistory } from "../hooks/useDecisionHistory";
import { dashboardMetrics } from "../utils/analytics";
import { formatLatency, formatPercent, numberFormatter } from "../utils/format";

export function Dashboard() {
  const { records, selectRecord } = useDecisionHistory();
  const metrics = dashboardMetrics(records);

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Total Decisions"
          value={numberFormatter.format(metrics.total)}
          detail="Analyst session volume"
          icon={Activity}
          tone="bg-blue-50 border-blue-100 text-blue-700"
        />
        <KpiCard
          label="Approved"
          value={numberFormatter.format(metrics.approved)}
          detail="Low-risk transactions released"
          icon={ShieldCheck}
          tone="bg-emerald-50 border-emerald-100 text-emerald-700"
        />
        <KpiCard
          label="Step-Up"
          value={numberFormatter.format(metrics.stepUp)}
          detail="Customer verification required"
          icon={Zap}
          tone="bg-orange-50 border-orange-100 text-orange-700"
        />
        <KpiCard
          label="Rejected"
          value={numberFormatter.format(metrics.rejected)}
          detail="High-risk transactions blocked"
          icon={TriangleAlert}
          tone="bg-rose-50 border-rose-100 text-rose-700"
        />
        <KpiCard
          label="Average Risk Score"
          value={formatPercent(metrics.averageRisk)}
          detail="Mean model score across decisions"
          icon={Gauge}
          tone="bg-blue-50 border-blue-100 text-blue-700"
        />
        <KpiCard
          label="Average Latency"
          value={formatLatency(metrics.averageLatency)}
          detail="End-to-end inference time"
          icon={Timer}
          tone="bg-zinc-100 border-zinc-200 text-zinc-700"
        />
        <KpiCard
          label="CAMARA Calls"
          value={numberFormatter.format(metrics.camaraCalls)}
          detail="Provider APIs used by the agent"
          icon={Network}
          tone="bg-orange-50 border-orange-100 text-orange-700"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <RiskDistributionChart records={records} />
        <DecisionPieChart records={records} />
        <LatencyHistogramChart records={records} />
        <CamaraUsageChart records={records} />
        <div className="xl:col-span-2">
          <DecisionTrendChart records={records} />
        </div>
      </section>

      <RecentDecisionsTable records={records.slice(0, 18)} onSelect={selectRecord} />
    </div>
  );
}
