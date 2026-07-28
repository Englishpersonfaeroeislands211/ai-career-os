import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/profile", label: "Profile" },
  { to: "/jobs/new", label: "Add job" },
  { to: "/settings", label: "Settings" },
];

export function AppNav() {
  return (
    <nav className="flex items-center gap-1">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          end={link.end}
          className={({ isActive }) =>
            `rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              isActive
                ? "bg-accent/15 text-accent"
                : "text-text-muted hover:bg-surface-overlay hover:text-text"
            }`
          }
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
