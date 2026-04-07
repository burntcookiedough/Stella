import { useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { getToken, login } from "./api/client";
import { AppShell } from "./components/AppShell";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { ChatPage } from "./pages/ChatPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ReportsPage } from "./pages/ReportsPage";

export default function App() {
  const [token, setTokenState] = useState(getToken());
  const [error, setError] = useState("");

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
    return <LoginScreen error={error} onLogin={handleLogin} />;
  }

  return (
    <Routes>
      <Route path="/" element={<AppShell onLogout={() => setTokenState(null)} />}>
        <Route index element={<OverviewPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="reports" element={<ReportsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function LoginScreen({
  error,
  onLogin,
}: {
  error: string;
  onLogin: (formData: FormData) => Promise<void>;
}) {
  return (
    <div className="login-shell">
      <section className="login-panel">
        <p className="eyebrow">Secure local access</p>
        <h1>Sign in to Stella</h1>
        <p className="muted-copy">
          Single-user JWT auth keeps the API safe on a home network while preserving the local-first
          model.
        </p>
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
