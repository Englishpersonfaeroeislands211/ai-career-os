interface OnboardingStepsProps {
  current: 1 | 2 | 3;
}

const STEPS = ["AI provider", "Upload resume", "Review"] as const;

export function OnboardingSteps({ current }: OnboardingStepsProps) {
  return (
    <ol className="flex items-center justify-center gap-2 text-sm">
      {STEPS.map((label, index) => {
        const step = index + 1;
        const active = step === current;
        const done = step < current;
        return (
          <li key={label} className="flex items-center gap-2">
            {index > 0 && <span className="text-border">→</span>}
            <span
              className={
                active
                  ? "font-medium text-accent"
                  : done
                    ? "text-text-muted"
                    : "text-text-muted/60"
              }
            >
              {step}. {label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
