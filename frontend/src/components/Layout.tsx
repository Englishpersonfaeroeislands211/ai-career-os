import { Link } from "react-router-dom";
import { Badge } from "./ui";

interface LayoutProps {
  children: React.ReactNode;
  subtitle?: string;
}

export function Layout({ children, subtitle = "Match Explorer" }: LayoutProps) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-surface-raised/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="group">
            <h1 className="text-lg font-semibold tracking-tight group-hover:text-accent">
              AI Career OS
            </h1>
            <p className="text-sm text-text-muted">{subtitle}</p>
          </Link>
          <Badge variant="info">M1</Badge>
        </div>
      </header>
      {children}
    </div>
  );
}
