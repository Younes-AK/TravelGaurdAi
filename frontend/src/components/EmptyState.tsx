import type { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-300 bg-white p-8 text-center shadow-card">
      <Icon className="mx-auto size-8 text-zinc-400" />
      <h3 className="mt-4 text-sm font-semibold text-zinc-950">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-zinc-500">{description}</p>
    </div>
  );
}
