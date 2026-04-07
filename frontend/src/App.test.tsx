import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-plotly.js", () => ({
  default: () => null,
}));

import App from "./App";

function renderWithProviders(initialEntries: string[] = ["/"]) {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("App", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/v1/overview")) {
          return new Response(
            JSON.stringify({
              available_users: ["fitbit-user"],
              selected_user: "fitbit-user",
              latest: {
                day: "2026-04-07",
                steps: 9000,
                sleep_minutes: 420,
                resting_hr: 58,
                hrv: 42,
                health_score: 84,
              },
              trend_slices: [],
              anomalies: [],
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        if (url.includes("/v1/analytics/correlations")) {
          return new Response(
            JSON.stringify({
              selected_user: "fitbit-user",
              matrix: {},
              pairs: [],
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response(JSON.stringify({ access_token: "token" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }),
    );
  });

  it("renders the login screen when no token is present", () => {
    renderWithProviders();
    expect(screen.getByRole("heading", { name: /sign in to stella/i })).toBeTruthy();
  });

  it("renders the analytics route when authenticated", async () => {
    window.localStorage.setItem("stella-token", "token");
    renderWithProviders(["/analytics"]);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /metric relationships/i })).toBeTruthy();
    });
  });
});
