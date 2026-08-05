export type Decision = "APPROVE" | "STEP_UP" | "REJECT";

export interface Transaction {
  transaction_id: string;
  amount: number;
  currency: string;
  merchant_country: string;
  merchant_name?: string;
  timestamp: string;
  device_id?: string;
  ip_address?: string;
}

export interface CustomerProfile {
  customer_id: string;
  home_country: string;
  trusted_devices: string[];
  last_sim_swap_days?: number;
  travel_frequency?: number;
  avg_transaction_amount?: number;
  phone_number?: string;
}

export type SignalMap = Record<string, unknown>;

export interface DecisionRequest {
  transaction: Transaction;
  customer_profile: CustomerProfile;
  signals?: SignalMap;
}

export interface DecisionResponse {
  decision: Decision;
  risk_score: number;
  confidence: number;
  explanation: string[];
  signals_used: string[];
  camara_calls: string[];
  network_signals: Record<string, any>;
  latency_ms: number;
  request_id: string;
}

export interface HealthResponse {
  status: string;
}

export interface ReadyResponse {
  status: string;
  provider: string;
  model: string;
}

export interface ApiErrorBody {
  error?: string;
  message?: string;
  detail?: unknown;
  request_id?: string;
}
