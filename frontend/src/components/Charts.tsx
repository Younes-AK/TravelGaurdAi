import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DecisionRecord } from "../types/dashboard";
import { camaraUsage, decisionPie, decisionTrend, latencyHistogram, riskDistribution } from "../utils/analytics";

const tooltipStyle = {
  background: "#ffffff",
  border: "1px solid #e5e7eb",
  borderRadius: 8,
  color: "#18181b",
  boxShadow: "0 8px 20px -14px rgba(16, 24, 40, 0.35)",
};

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-card">
      <h3 className="text-sm font-semibold text-zinc-950">{title}</h3>
      <div className="mt-4 h-64">{children}</div>
    </div>
  );
}

export function RiskDistributionChart({ records }: { records: DecisionRecord[] }) {
  return (
    <ChartCard title="Risk score distribution">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={riskDistribution(records)}>
          <CartesianGrid stroke="#eef2f7" vertical={false} />
          <XAxis dataKey="range" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f8fafc" }} />
          <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function DecisionPieChart({ records }: { records: DecisionRecord[] }) {
  const data = decisionPie(records);
  return (
    <ChartCard title="Decision mix">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} innerRadius={58} outerRadius={88} paddingAngle={4} dataKey="value">
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function LatencyHistogramChart({ records }: { records: DecisionRecord[] }) {
  return (
    <ChartCard title="Latency histogram">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={latencyHistogram(records)}>
          <CartesianGrid stroke="#eef2f7" vertical={false} />
          <XAxis dataKey="range" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f8fafc" }} />
          <Bar dataKey="count" fill="#10b981" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function CamaraUsageChart({ records }: { records: DecisionRecord[] }) {
  return (
    <ChartCard title="CAMARA API usage">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={camaraUsage(records)} layout="vertical" margin={{ left: 12 }}>
          <CartesianGrid stroke="#eef2f7" horizontal={false} />
          <XAxis type="number" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis dataKey="api" type="category" width={120} stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f8fafc" }} />
          <Bar dataKey="count" fill="#f97316" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function DecisionTrendChart({ records }: { records: DecisionRecord[] }) {
  return (
    <ChartCard title="Decision trend">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={decisionTrend(records)}>
          <CartesianGrid stroke="#eef2f7" vertical={false} />
          <XAxis dataKey="label" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Area type="monotone" dataKey="risk" stroke="#2563eb" fill="#2563eb" fillOpacity={0.1} />
          <Line type="monotone" dataKey="latency" stroke="#f97316" dot={false} yAxisId={0} opacity={0.7} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
