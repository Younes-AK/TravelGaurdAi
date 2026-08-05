import { formatPercent } from "../utils/format";

export function RiskGauge({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(1, value));
  const x = `${clamped * 100}%`;

  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-zinc-900">Risk gauge</p>
          <p className="text-xs text-zinc-500">Model output normalized from 0 to 1</p>
        </div>
        <p className="text-2xl font-semibold tracking-tight text-zinc-950">{formatPercent(clamped)}</p>
      </div>
      <div className="relative mt-6 h-2 overflow-visible rounded-full bg-zinc-100">
        <div className="flex h-2 overflow-hidden rounded-full">
          <span className="h-full flex-1 bg-emerald-500" />
          <span className="h-full flex-1 bg-orange-500" />
          <span className="h-full flex-1 bg-rose-500" />
        </div>
        <div
          style={{ left: x }}
          className="absolute top-1/2 size-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-zinc-900 shadow-card"
        />
      </div>
      <div className="mt-3 flex justify-between text-xs text-zinc-500">
        <span>0</span>
        <span>1</span>
      </div>
    </div>
  );
}
