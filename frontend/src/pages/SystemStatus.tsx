import { Activity, Cpu, DatabaseZap, Server, WifiOff } from "lucide-react";

import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { useHealthQuery, useReadyQuery } from "../hooks/useTravelGuardApi";

function StatusTile({
  label,
  value,
  ok,
  icon: Icon,
}: {
  label: string;
  value: string;
  ok: boolean;
  icon: typeof Activity;
}) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-zinc-500">{label}</p>
          <p className="mt-2 text-lg font-semibold text-zinc-950">{value}</p>
        </div>
        <div className={`rounded-lg border p-2 ${ok ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50"}`}>
          <Icon className={`size-5 ${ok ? "text-emerald-700" : "text-rose-700"}`} />
        </div>
      </div>
    </div>
  );
}

export function SystemStatus() {
  const health = useHealthQuery();
  const ready = useReadyQuery();
  const online = health.data?.status === "ok";
  const readyOk = ready.data?.status === "ready";

  return (
    <div className="space-y-6">
      {health.isLoading || ready.isLoading ? <LoadingSkeleton rows={2} /> : null}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatusTile label="Backend Online" value={online ? "Online" : "Offline"} ok={online} icon={online ? Server : WifiOff} />
        <StatusTile label="API Status" value={readyOk ? "Ready" : "Not ready"} ok={readyOk} icon={Activity} />
        <StatusTile label="Provider" value={ready.data?.provider || "Unavailable"} ok={readyOk} icon={DatabaseZap} />
        <StatusTile label="Model" value={ready.data?.model || "Unavailable"} ok={readyOk} icon={Cpu} />
      </section>
      <section className="rounded-lg border border-line bg-white p-5 shadow-card">
        <h2 className="text-lg font-semibold text-zinc-950">Service checks</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <pre className="overflow-auto rounded-lg border border-line bg-zinc-50 p-4 text-sm text-zinc-700">
            {JSON.stringify(health.data || { error: health.error instanceof Error ? health.error.message : "No health response" }, null, 2)}
          </pre>
          <pre className="overflow-auto rounded-lg border border-line bg-zinc-50 p-4 text-sm text-zinc-700">
            {JSON.stringify(ready.data || { error: ready.error instanceof Error ? ready.error.message : "No readiness response" }, null, 2)}
          </pre>
        </div>
      </section>
    </div>
  );
}
