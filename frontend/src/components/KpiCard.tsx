import type { LucideIcon } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone: string;
}

export function KpiCard({ label, value, detail, icon: Icon, tone }: KpiCardProps) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-card transition hover:border-zinc-300">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{label}</p>
          <p className="mt-3 text-2xl font-semibold tracking-tight text-zinc-950">{value}</p>
        </div>
        <div className={`rounded-lg border p-2.5 ${tone}`}>
          <Icon className="size-5" />
        </div>
      </div>
      <p className="mt-4 text-sm text-zinc-500">{detail}</p>
    </div>
  );
}
