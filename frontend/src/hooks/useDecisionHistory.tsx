import { createContext, useContext, useMemo, useState } from "react";

import type { DecisionRequest, DecisionResponse } from "../types/api";
import type { DecisionRecord } from "../types/dashboard";
import { seedDecisionHistory } from "../utils/demoData";

interface DecisionHistoryContextValue {
  records: DecisionRecord[];
  addDecision: (request: DecisionRequest, response: DecisionResponse, source: DecisionRecord["source"]) => DecisionRecord;
  selectedRecord?: DecisionRecord;
  selectRecord: (record: DecisionRecord) => void;
}

const storageKey = "travelguard.decisionHistory";
const DecisionHistoryContext = createContext<DecisionHistoryContextValue | undefined>(undefined);

function readInitialRecords() {
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (raw) {
      return JSON.parse(raw) as DecisionRecord[];
    }
  } catch {
    window.localStorage.removeItem(storageKey);
  }
  return seedDecisionHistory();
}

export function DecisionHistoryProvider({ children }: { children: React.ReactNode }) {
  const [records, setRecords] = useState<DecisionRecord[]>(readInitialRecords);
  const [selectedId, setSelectedId] = useState<string | undefined>(records[0]?.id);

  const value = useMemo<DecisionHistoryContextValue>(() => {
    const selectedRecord = records.find((record) => record.id === selectedId) || records[0];

    return {
      records,
      selectedRecord,
      selectRecord: (record) => setSelectedId(record.id),
      addDecision: (request, response, source) => {
        const record: DecisionRecord = {
          id: crypto.randomUUID(),
          createdAt: new Date().toISOString(),
          request,
          response,
          source,
        };
        setRecords((current) => {
          const next = [record, ...current].slice(0, 80);
          window.localStorage.setItem(storageKey, JSON.stringify(next));
          return next;
        });
        setSelectedId(record.id);
        return record;
      },
    };
  }, [records, selectedId]);

  return <DecisionHistoryContext.Provider value={value}>{children}</DecisionHistoryContext.Provider>;
}

export function useDecisionHistory() {
  const context = useContext(DecisionHistoryContext);
  if (!context) {
    throw new Error("useDecisionHistory must be used within DecisionHistoryProvider");
  }
  return context;
}
