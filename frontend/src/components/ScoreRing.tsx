interface ScoreRingProps {
  score: number | null;
  size?: "sm" | "md" | "lg";
  label?: string;
}

export function ScoreRing({ score, size = "md", label = "match" }: ScoreRingProps) {
  if (score == null) {
    return (
      <div className="flex flex-col items-center gap-0.5 text-text-muted">
        <span
          className={`flex items-center justify-center rounded-full border border-dashed border-border font-semibold tabular-nums ${
            size === "lg" ? "size-16 text-lg" : size === "sm" ? "size-10 text-xs" : "size-14 text-base"
          }`}
        >
          —
        </span>
        {label && <span className="text-[10px] uppercase tracking-wide">{label}</span>}
      </div>
    );
  }

  const pct = Math.round(score);
  const color = pct >= 70 ? "text-success" : pct >= 40 ? "text-warning" : "text-danger";
  const ring =
    pct >= 70 ? "border-success/40" : pct >= 40 ? "border-warning/40" : "border-danger/40";

  return (
    <div className="flex flex-col items-center gap-0.5">
      <span
        className={`flex items-center justify-center rounded-full border-2 bg-surface font-bold tabular-nums ${color} ${ring} ${
          size === "lg" ? "size-16 text-xl" : size === "sm" ? "size-10 text-sm" : "size-14 text-lg"
        }`}
      >
        {pct}
      </span>
      {label && <span className="text-[10px] uppercase tracking-wide text-text-muted">{label}</span>}
    </div>
  );
}
