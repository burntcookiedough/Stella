import { NavLink, Outlet, useLocation } from "react-router-dom";
import { motion } from "framer-motion";

import { clearToken, type ReadyStateResponse } from "../api/client";
import { ImportPanel } from "./ImportPanel";

const NAV_ITEMS = [
  { to: "/", label: "Overview" },
  { to: "/chat", label: "Chat" },
  { to: "/analytics", label: "Deep Analytics" },
  { to: "/reports", label: "Reports" },
];

export function AppShell({
  onLogout,
  runtime,
  runtimeError,
}: {
  onLogout: () => void;
  runtime?: ReadyStateResponse;
  runtimeError: Error | null;
}) {
  const location = useLocation();
  const backendLabel = runtimeError ? "backend offline" : runtime ? "backend ready" : "checking backend";
  const dataLabel = runtime?.has_data ? "data loaded" : "waiting for import";
  const aiLabel = runtimeError ? "runtime blocked" : runtime?.llm_reachable ? "llm ready" : "metrics-only mode";
  const runtimeMessage = runtimeError
    ? "The backend readiness check failed. Restart Stella from the supported launcher to restore the workspace."
    : !runtime
      ? "Checking workspace readiness..."
      : !runtime.has_data
        ? "No health data has been imported yet. Use the import panel to load an export bundle before analytics, reports, or chat become useful."
        : runtime.llm_reachable
          ? `Ollama is reachable with ${runtime.llm_model}.`
          : `Chat is intentionally unavailable while ${runtime.llm_provider} is down. Reports stay usable in metrics-only mode: ${runtime.llm_error}`;

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
              Import a health export, review the active dataset, and generate a clean local handoff
              without leaving the core workspace.
            </p>
            <div className="runtime-banner">
              <div className="runtime-pill-row">
                <p className={`status-pill ${runtimeError ? "error" : "ready"}`}>{backendLabel}</p>
                <p className={`status-pill ${runtime?.has_data ? "ready" : "warning"}`}>{dataLabel}</p>
                <p className={`status-pill ${runtimeError ? "error" : runtime?.llm_reachable ? "ready" : "warning"}`}>
                  {aiLabel}
                </p>
              </div>
              <p className="status">{runtimeMessage}</p>
            </div>
          </div>
          <ImportPanel hasData={Boolean(runtime?.has_data)} />
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
