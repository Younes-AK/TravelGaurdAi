import { useMutation, useQuery } from "@tanstack/react-query";

import { travelGuardApi } from "../services/api";
import type { DecisionRequest } from "../types/api";

export function useHealthQuery() {
  return useQuery({
    queryKey: ["health"],
    queryFn: travelGuardApi.health,
    refetchInterval: 10000,
  });
}

export function useReadyQuery() {
  return useQuery({
    queryKey: ["ready"],
    queryFn: travelGuardApi.ready,
    refetchInterval: 10000,
    retry: 1,
  });
}

export function useDecisionMutation() {
  return useMutation({
    mutationFn: (payload: DecisionRequest) => travelGuardApi.decide(payload),
  });
}
