import clsx from "clsx";
import { CheckCircle2, Info, XCircle } from "lucide-react";

import { useToast } from "../hooks/useToast";

const icons = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
};

export function ToastViewport() {
  const { toasts, removeToast } = useToast();

  return (
    <div className="fixed right-4 top-4 z-50 w-[min(360px,calc(100vw-2rem))] space-y-3">
      {toasts.map((toast) => {
        const Icon = icons[toast.tone];
        return (
          <button
            key={toast.id}
            type="button"
            onClick={() => removeToast(toast.id)}
            className="w-full rounded-lg border border-line bg-white p-4 text-left shadow-glow transition hover:bg-zinc-50"
          >
            <div className="flex gap-3">
              <Icon
                className={clsx(
                  "mt-0.5 size-5",
                  toast.tone === "success" && "text-emerald-600",
                  toast.tone === "error" && "text-rose-600",
                  toast.tone === "info" && "text-blue-600",
                )}
              />
              <div>
                <p className="text-sm font-semibold text-zinc-950">{toast.title}</p>
                {toast.description ? <p className="mt-1 text-sm text-zinc-500">{toast.description}</p> : null}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
