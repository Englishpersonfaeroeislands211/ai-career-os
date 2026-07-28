import { Link } from "react-router-dom";
import { AppNav } from "./AppNav";

interface LayoutProps {
  children: React.ReactNode;
  subtitle?: string;
  showNav?: boolean;
}

export function Layout({ children, subtitle = "Career command center", showNav = true }: LayoutProps) {
  return (
    <div className="min-h-screen bg-surface">
      <header className="sticky top-0 z-10 border-b border-border bg-surface-raised/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <Link to="/" className="group min-w-0">
            <h1 className="text-lg font-semibold tracking-tight group-hover:text-accent">
              AI Career OS
            </h1>
            <p className="truncate text-sm text-text-muted">{subtitle}</p>
          </Link>
          {showNav && <AppNav />}
        </div>
      </header>
      {children}
    </div>
  );
}
