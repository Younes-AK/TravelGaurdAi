import { createContext, useCallback, useContext, useMemo, useState } from "react";

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  tone: "success" | "error" | "info";
}

interface ToastContextValue {
  toasts: ToastMessage[];
  pushToast: (toast: Omit<ToastMessage, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = useCallback(
    (toast: Omit<ToastMessage, "id">) => {
      const id = crypto.randomUUID();
      setToasts((current) => [{ ...toast, id }, ...current].slice(0, 4));
      window.setTimeout(() => removeToast(id), 4200);
    },
    [removeToast],
  );

  const value = useMemo(() => ({ toasts, pushToast, removeToast }), [pushToast, removeToast, toasts]);

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
