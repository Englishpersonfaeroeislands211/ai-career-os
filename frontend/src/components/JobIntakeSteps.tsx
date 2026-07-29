interface JobIntakeStepsProps {
  current: 1 | 2;
}

const STEPS = [
  { num: 1, label: "Paste" },
  { num: 2, label: "Review" },
] as const;

export function JobIntakeSteps({ current }: JobIntakeStepsProps) {
  return (
    <ol className="flex items-center justify-center gap-0">
      {STEPS.map((step, index) => {
        const active = step.num === current;
        const done = step.num < current;
        return (
          <li key={step.num} className="flex items-center">
            {index > 0 && (
              <span
                className={`mx-2 h-px w-8 sm:w-12 ${done ? "bg-accent" : "bg-border"}`}
                aria-hidden
              />
            )}
            <span className="flex items-center gap-2">
              <span
                className={`flex size-7 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
                  active
                    ? "bg-accent text-white"
                    : done
                      ? "bg-accent/20 text-accent"
                      : "bg-surface-overlay text-text-muted"
                }`}
              >
                {done ? "✓" : step.num}
              </span>
              <span
                className={
                  active ? "font-medium text-text" : done ? "text-text-muted" : "text-text-muted/60"
                }
              >
                {step.label}
              </span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
