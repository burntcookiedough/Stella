import { NavLink, Outlet, useLocation } from "react-router-dom";
import { motion } from "framer-motion";

import { clearToken } from "../api/client";
import { ImportPanel } from "./ImportPanel";

const NAV_ITEMS = [
  { to: "/", label: "Overview" },
  { to: "/chat", label: "Chat" },
  { to: "/analytics", label: "Deep Analytics" },
  { to: "/reports", label: "Reports" },
];

export function AppShell({
  onLogout,
}: {
  onLogout: () => void;
}) {
  const location = useLocation();

  return (
    <div className="shell">
      <div className="shell-glow shell-glow-left" />
      <div className="shell-glow shell-glow-right" />
      <aside className="sidebar">
        <div className="brand-block">
          <p className="eyebrow">Stella v2</p>
          <h1>Health intelligence, local by default.</h1>
          <p className="sidebar-copy">
            Unified imports, deterministic analytics, and a swappable model runtime without
            sending your health data to the cloud.
          </p>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
          <motion.div
            className="route-indicator"
            layout
            transition={{ type: "spring", stiffness: 260, damping: 28 }}
            key={location.pathname}
          />
        </nav>

        <button
          type="button"
          className="ghost-button"
          onClick={() => {
            clearToken();
            onLogout();
          }}
        >
          Log out
        </button>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div className="workspace-intro">
            <p className="eyebrow">Workspace</p>
            <h2>Selected KPIs, streaming insight, and trend depth.</h2>
            <p className="workspace-copy">
              Review the active dataset, ask focused questions, and export a clean handoff without
              leaving the core workspace.
            </p>
          </div>
          <ImportPanel />
        </header>
        <motion.section
          className="workspace-body"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
        >
          <Outlet />
        </motion.section>
      </main>
    </div>
  );
}
