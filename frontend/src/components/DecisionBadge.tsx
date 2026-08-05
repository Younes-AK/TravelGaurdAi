import clsx from "clsx";

import type { Decision } from "../types/api";
import { decisionTone } from "../utils/format";

export function DecisionBadge({ decision, large = false }: { decision: Decision; large?: boolean }) {
  const tone = decisionTone(decision);
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-2 rounded-md border font-semibold",
        tone.badge,
        large ? "px-3 py-2 text-sm" : "px-2.5 py-1 text-xs",
      )}
    >
      <span className={clsx("size-1.5 rounded-full", tone.dot)} />
      {tone.label}
    </span>
  );
}
