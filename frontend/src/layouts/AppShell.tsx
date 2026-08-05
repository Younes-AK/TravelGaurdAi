import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import clsx from "clsx";
import {
  Activity,
  BookOpen,
  Gauge,
  History,
  LayoutDashboard,
  Play,
  Radio,
  Shield,
  Square,
} from "lucide-react";

import { useDecisionHistory } from "../hooks/useDecisionHistory";
import { useDecisionMutation } from "../hooks/useTravelGuardApi";
import { useToast } from "../hooks/useToast";
import { createRandomDecisionRequest } from "../utils/demoData";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/simulator", label: "Decision Simulator", icon: Gauge },
  { to: "/history", label: "Decision History", icon: History },
  { to: "/status", label: "System Status", icon: Activity },
  { to: "/docs", label: "API Documentation", icon: BookOpen },
];

const pageTitles: Record<string, string> = {
  "/": "Real-time decision operations",
  "/simulator": "Decision simulator",
  "/history": "Decision history",
  "/status": "System status",
  "/docs": "API documentation",
};

export function AppShell() {
  const location = useLocation();
  const [liveMode, setLiveMode] = useState(false);
  const { addDecision } = useDecisionHistory();
  const { pushToast } = useToast();
  const mutation = useDecisionMutation();

  useEffect(() => {
    if (!liveMode) return undefined;

    const run = async () => {
      const payload = createRandomDecisionRequest("live");
      try {
        const response = await mutation.mutateAsync(payload);
        addDecision(payload, response, "live-demo");
        pushToast({
          tone: "success",
          title: `${response.decision.replace("_", "-")} decision completed`,
          description: `${response.request_id} returned in ${response.latency_ms.toFixed(1)} ms`,
        });
      } catch (error) {
        pushToast({
          tone: "error",
          title: "Live demo request failed",
          description: error instanceof Error ? error.message : "Backend did not return a decision.",
        });
      }
    };

    run();
    const interval = window.setInterval(run, 5000);
    return () => window.clearInterval(interval);
  }, [addDecision, liveMode, mutation, pushToast]);

  return (
    <div className="min-h-screen bg-panel text-zinc-800">
      <div className="relative min-h-screen">
        <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-line bg-white p-5 lg:block">
          <div className="flex items-center gap-3 px-1 py-2">
            <div className="flex size-10 items-center justify-center rounded-lg border border-blue-100 bg-blue-50">
              <Shield className="size-5 text-blue-700" />
            </div>
            <div>
              <p className="text-sm font-semibold text-zinc-950">TravelGuard AI</p>
              <p className="text-xs text-zinc-500">Bank risk operations</p>
            </div>
          </div>
          <nav className="mt-8 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
                    isActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-950",
                  )
                }
              >
                <item.icon className="size-4" />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="absolute bottom-5 left-5 right-5 rounded-lg border border-line bg-zinc-50 p-4 shadow-card">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-800">
              <Radio className="size-4 text-emerald-500" />
              Live Demo
            </div>
            <p className="mt-2 text-sm text-zinc-500">Generate and score a bank transaction every 5 seconds.</p>
            <button
              type="button"
              onClick={() => setLiveMode((value) => !value)}
              className={clsx(
                "mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition",
                liveMode
                  ? "border-rose-200 bg-rose-50 text-rose-700"
                  : "border-blue-600 bg-blue-600 text-white hover:bg-blue-700",
              )}
            >
              {liveMode ? <Square className="size-4" /> : <Play className="size-4" />}
              {liveMode ? "Stop live mode" : "Start live mode"}
            </button>
          </div>
        </aside>
        <main className="min-w-0 lg:pl-72">
          <header className="sticky top-0 z-30 border-b border-line bg-white px-4 py-4 md:px-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700">TravelGuard AI</p>
                <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-950">{pageTitles[location.pathname] || "Dashboard"}</h1>
              </div>
              <div className="flex items-center gap-2 overflow-x-auto lg:hidden">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      clsx(
                        "inline-flex size-10 shrink-0 items-center justify-center rounded-lg border border-line transition",
                        isActive ? "bg-blue-50 text-blue-700" : "bg-white text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900",
                      )
                    }
                    aria-label={item.label}
                  >
                    <item.icon className="size-4" />
                  </NavLink>
                ))}
              </div>
              <button
                type="button"
                onClick={() => setLiveMode((value) => !value)}
                className={clsx(
                  "hidden items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition md:inline-flex",
                  liveMode
                    ? "border-rose-200 bg-rose-50 text-rose-700"
                    : "border-line bg-white text-zinc-700 hover:bg-zinc-50",
                )}
              >
                <span className={clsx("size-2 rounded-full", liveMode ? "bg-emerald-500" : "bg-zinc-400")} />
                {liveMode ? "Live demo running" : "Start live demo"}
              </button>
            </div>
          </header>
          <div className="p-4 md:p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
