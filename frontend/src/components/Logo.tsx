import { Link } from "react-router-dom";

interface LogoProps {
  compact?: boolean;
  className?: string;
  linkTo?: string;
}

export function LogoMark({ className = "size-8" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
    >
      <rect width="32" height="32" rx="8" fill="#0f766e" />
      <path
        d="M8 22V12l4 3 4-5 4 4 4-6v14"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.95"
      />
      <circle cx="22" cy="9" r="2" fill="#99f6e4" />
    </svg>
  );
}

export function Logo({ compact = false, className = "", linkTo = "/" }: LogoProps) {
  const content = (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <LogoMark className="size-8 shrink-0" />
      {!compact && (
        <span className="min-w-0 text-left leading-tight">
          <span className="block text-sm font-semibold tracking-tight text-text">Career OS</span>
          <span className="block text-[10px] font-medium uppercase tracking-wider text-text-muted">
            Career matching
          </span>
        </span>
      )}
    </span>
  );

  if (linkTo) {
    return (
      <Link to={linkTo} className="rounded-lg outline-none ring-accent focus-visible:ring-2">
        {content}
      </Link>
    );
  }

  return content;
}
