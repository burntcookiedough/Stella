import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { downloadReport, fetchOverview } = vi.hoisted(() => ({
  downloadReport: vi.fn(),
  fetchOverview: vi.fn(),
}));

vi.mock("../api/client", () => ({
  downloadReport,
  fetchOverview,
}));

import { ReportsPage } from "./ReportsPage";

function renderPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <ReportsPage
        runtime={{
          status: "ready",
          has_data: true,
          llm_provider: "stub",
          llm_model: "test-model",
          llm_reachable: true,
          llm_error: null,
        }}
      />
    </QueryClientProvider>,
  );
}

describe("ReportsPage", () => {
  beforeEach(() => {
    downloadReport.mockReset();
    fetchOverview.mockReset();
    fetchOverview.mockResolvedValue({
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
    });
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:report"),
      revokeObjectURL: vi.fn(),
    });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows degraded success messaging when the LLM summary falls back", async () => {
    downloadReport.mockResolvedValue({
      blob: new Blob(["pdf"], { type: "application/pdf" }),
      fileName: "stella-report-fitbit-user.pdf",
      llmStatus: "fallback",
      llmError: "ollama timed out while handling report_summary.",
    });

    renderPage();

    const button = await screen.findByRole("button", { name: /download report/i });
    await waitFor(() => expect(button.hasAttribute("disabled")).toBe(false));
    fireEvent.click(button);

    expect(
      await screen.findByText(/metrics-only report downloaded because the llm summary was unavailable/i),
    ).toBeTruthy();
  });

  it("shows a failure when report generation fails", async () => {
    downloadReport.mockRejectedValue(new Error("report request failed"));

    renderPage();

    const button = await screen.findByRole("button", { name: /download report/i });
    await waitFor(() => expect(button.hasAttribute("disabled")).toBe(false));
    fireEvent.click(button);

    expect(await screen.findByText(/report request failed/i)).toBeTruthy();
  });

  it("explains that metrics-only PDFs are still expected", async () => {
    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <ReportsPage
          runtime={{
            status: "ready",
            has_data: true,
            llm_provider: "ollama",
            llm_model: "mistral",
            llm_reachable: false,
            llm_error: "provider unavailable",
          }}
        />
      </QueryClientProvider>,
    );

    expect(await screen.findByText(/metrics-only reports are expected right now/i)).toBeTruthy();
  });
});
