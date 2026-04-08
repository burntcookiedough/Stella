import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { fetchOverview } = vi.hoisted(() => ({
  fetchOverview: vi.fn(),
}));

vi.mock("../api/client", () => ({
  fetchOverview,
}));

import { OverviewPage } from "./OverviewPage";

describe("OverviewPage", () => {
  beforeEach(() => {
    fetchOverview.mockReset();
  });

  it("shows an onboarding empty state before data is imported", async () => {
    fetchOverview.mockResolvedValue({
      available_users: [],
      selected_user: null,
      latest: null,
      trend_slices: [],
      anomalies: [],
    });

    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <OverviewPage
          runtime={{
            status: "ready",
            has_data: false,
            llm_provider: "ollama",
            llm_model: "mistral",
            llm_reachable: false,
            llm_error: "provider unavailable",
          }}
        />
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: /stella is ready for your first import/i })).toBeTruthy();
    expect(screen.getByText(/metrics-only mode is expected until the optional model runtime is available/i)).toBeTruthy();
  });
});
