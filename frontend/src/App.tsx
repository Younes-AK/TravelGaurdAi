import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { ToastViewport } from "./components/ToastViewport";
import { DecisionHistoryProvider } from "./hooks/useDecisionHistory";
import { ToastProvider } from "./hooks/useToast";
import { AppShell } from "./layouts/AppShell";
import { ApiDocumentation } from "./pages/ApiDocumentation";
import { Dashboard } from "./pages/Dashboard";
import { DecisionHistory } from "./pages/DecisionHistory";
import { DecisionSimulator } from "./pages/DecisionSimulator";
import { SystemStatus } from "./pages/SystemStatus";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5000,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <DecisionHistoryProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<AppShell />}>
                <Route index element={<Dashboard />} />
                <Route path="simulator" element={<DecisionSimulator />} />
                <Route path="history" element={<DecisionHistory />} />
                <Route path="status" element={<SystemStatus />} />
                <Route path="docs" element={<ApiDocumentation />} />
              </Route>
            </Routes>
          </BrowserRouter>
          <ToastViewport />
        </DecisionHistoryProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
