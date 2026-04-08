import { Suspense, lazy, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Navigate, Route, Routes } from "react-router-dom";

import { fetchReadyState, getToken, login, type ReadyStateResponse } from "./api/client";
import { AppShell } from "./components/AppShell";

const OverviewPage = lazy(async () => import("./pages/OverviewPage").then((module) => ({ default: module.OverviewPage })));
const ChatPage = lazy(async () => import("./pages/ChatPage").then((module) => ({ default: module.ChatPage })));
const AnalyticsPage = lazy(async () =>
  import("./pages/AnalyticsPage").then((module) => ({ default: module.AnalyticsPage })),
);
const ReportsPage = lazy(async () => import("./pages/ReportsPage").then((module) => ({ default: module.ReportsPage })));

export default function App() {
  const [token, setTokenState] = useState(getToken());
  const [error, setError] = useState("");
  const runtime = useQuery<ReadyStateResponse, Error>({
    queryKey: ["readyz"],
    queryFn: fetchReadyState,
    retry: false,
    refetchInterval: 30_000,
  });

  const authenticated = useMemo(() => Boolean(token), [token]);

  async function handleLogin(formData: FormData): Promise<void> {
    try {
      setError("");
      await login({
        username: String(formData.get("username") ?? ""),
        password: String(formData.get("password") ?? ""),
      });
      setTokenState(getToken());
    } catch (loginError) {
      setError(String(loginError));
    }
  }

  if (!authenticated) {
    return <LoginScreen error={error} onLogin={handleLogin} runtime={runtime.data} runtimeError={runtime.error} />;
  }

  return (
    <Suspense fallback={<p className="status">Loading workspace...</p>}>
      <Routes>
        <Route
          path="/"
          element={<AppShell onLogout={() => setTokenState(null)} runtime={runtime.data} runtimeError={runtime.error} />}
        >
          <Route index element={<OverviewPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="reports" element={<ReportsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

function LoginScreen({
  error,
  onLogin,
  runtime,
  runtimeError,
}: {
  error: string;
  onLogin: (formData: FormData) => Promise<void>;
  runtime?: ReadyStateResponse;
  runtimeError: Error | null;
}) {
  const runtimeTone = runtimeError
    ? "error"
    : runtime && !runtime.llm_reachable
      ? "warning"
      : "ok";

  return (
    <div className="login-shell">
      <section className="login-panel">
        <p className="eyebrow">Secure local access</p>
        <h1>Sign in to Stella</h1>
        <p className="muted-copy">
          Single-user JWT auth keeps the API safe on a home network while preserving the local-first
          model.
        </p>
        <div className={`runtime-card ${runtimeTone}`}>
          <p className="control-label">Runtime status</p>
          {runtimeError ? (
            <p className="status error">
              Backend unavailable. Start Stella with <code>run_stella.bat</code> or <code>run_stella_docker.bat</code>.
            </p>
          ) : runtime ? (
            <>
              <p className="status">
                Backend ready. LLM provider: {runtime.llm_provider} / {runtime.llm_model}
              </p>
              {!runtime.has_data ? (
                <p className="muted-copy">No imported data yet. Sign in, then use Import to load a source bundle.</p>
              ) : null}
              {!runtime.llm_reachable ? (
                <p className="status warning">
                  Stella will stay usable in metrics-only mode until the model runtime recovers: {runtime.llm_error}
                </p>
              ) : null}
            </>
          ) : (
            <p className="status">Checking local services...</p>
          )}
        </div>
        <form
          className="login-form"
          onSubmit={(event) => {
            event.preventDefault();
            void onLogin(new FormData(event.currentTarget));
          }}
        >
          <input name="username" placeholder="Username" defaultValue="stella" />
          <input name="password" type="password" placeholder="Password" defaultValue="stella" />
          <button type="submit">Enter workspace</button>
        </form>
        {error ? <p className="status error">{error}</p> : null}
      </section>
    </div>
  );
}
