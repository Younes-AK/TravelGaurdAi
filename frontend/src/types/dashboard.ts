import type { DecisionRequest, DecisionResponse } from "./api";

export interface DecisionRecord {
  id: string;
  createdAt: string;
  request: DecisionRequest;
  response: DecisionResponse;
  source: "seed" | "simulator" | "live-demo";
}

export interface TimelineStep {
  id: string;
  title: string;
  description: string;
  status: "complete" | "active" | "pending" | "error";
  meta?: string;
}
