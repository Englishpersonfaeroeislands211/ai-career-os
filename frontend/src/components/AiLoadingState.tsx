import { useEffect, useState } from "react";
import {
  LOADING_CONFIG,
  type AiLoadingVariant,
  type LoadingStep,
} from "../lib/loadingMessages";

interface AiLoadingStateProps {
  variant: AiLoadingVariant;
  size?: "sm" | "md" | "lg";
  className?: string;
}

function useRotatingMessage(messages: string[], intervalMs = 2800) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
    if (messages.length <= 1) return;
    const id = window.setInterval(
      () => setIndex((current) => (current + 1) % messages.length),
      intervalMs,
    );
    return () => window.clearInterval(id);
  }, [messages, intervalMs]);

  return messages[index] ?? messages[0];
}

function StepIndicator({ steps, activeIndex }: { steps: LoadingStep[]; activeIndex: number }) {
  return (
    <div className="flex items-center justify-center gap-1">
      {steps.map((step, index) => {
        const done = index < activeIndex;
        const active = index === activeIndex;
        return (
          <div key={step.label} className="flex items-center gap-1">
            {index > 0 && (
              <span
                className={`h-px w-4 sm:w-6 ${done ? "bg-accent" : "bg-border"}`}
                aria-hidden
              />
            )}
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide transition-colors ${
                done
                  ? "bg-accent/20 text-accent"
                  : active
                    ? "bg-accent text-white"
                    : "bg-surface-overlay text-text-muted"
              }`}
            >
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function AiLoadingState({ variant, size = "md", className = "" }: AiLoadingStateProps) {
  const config = LOADING_CONFIG[variant];
  const message = useRotatingMessage(config.messages);
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!config.steps?.length) return;
    setStepIndex(0);
    const id = window.setInterval(
      () => setStepIndex((current) => (current + 1) % config.steps!.length),
      3200,
    );
    return () => window.clearInterval(id);
  }, [config.steps, variant]);

  const padding = size === "sm" ? "py-6 px-4" : size === "lg" ? "py-14 px-8" : "py-10 px-6";

  return (
    <div
      className={`relative overflow-hidden rounded-xl border border-border bg-surface-raised shadow-sm ${padding} ${className}`}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="ai-shimmer-bar absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-accent/50 to-transparent" />

      <div className="relative flex flex-col items-center text-center">
        <div className="relative mb-5 flex size-14 items-center justify-center">
          <span className="relative flex size-10 items-center justify-center rounded-full border border-border bg-surface-overlay">
            <span className="size-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          </span>
        </div>

        <p className="text-sm font-semibold text-text">{config.title}</p>
        <p
          key={message}
          className="ai-message-fade mt-2 max-w-md text-sm leading-relaxed text-text-muted"
        >
          {message}
        </p>

        {config.steps && config.steps.length > 0 && (
          <div className="mt-6 w-full max-w-sm">
            <StepIndicator steps={config.steps} activeIndex={stepIndex} />
          </div>
        )}

        <div className="mt-5 flex gap-1" aria-hidden>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="size-1.5 rounded-full bg-accent/60 animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export function PageLoader({ variant = "page" }: { variant?: AiLoadingVariant }) {
  return (
    <div className="flex min-h-[50vh] items-center justify-center p-6">
      <div className="w-full max-w-lg">
        <AiLoadingState variant={variant} size="lg" />
      </div>
    </div>
  );
}
