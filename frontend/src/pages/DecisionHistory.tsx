import { FileText } from "lucide-react";

import { DecisionTimeline } from "../components/DecisionTimeline";
import { EmptyState } from "../components/EmptyState";
import { RecentDecisionsTable } from "../components/RecentDecisionsTable";
import { useDecisionHistory } from "../hooks/useDecisionHistory";

export function DecisionHistory() {
  const { records, selectedRecord, selectRecord } = useDecisionHistory();

  return (
    <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <RecentDecisionsTable records={records} onSelect={selectRecord} />
      <div className="space-y-4">
        {selectedRecord ? (
          <>
            <DecisionTimeline record={selectedRecord} />
            <div className="rounded-lg border border-line bg-white p-5 shadow-card">
              <h2 className="text-lg font-semibold text-zinc-950">Explainability</h2>
              <div className="mt-4 space-y-2">
                {selectedRecord.response.explanation.map((item) => (
                  <div key={item} className="rounded-lg border border-line bg-zinc-50 px-3 py-2 text-sm text-zinc-700">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <EmptyState
            icon={FileText}
            title="No decision selected"
            description="Choose a transaction from the history table to inspect its timeline and explanations."
          />
        )}
      </div>
    </div>
  );
}
