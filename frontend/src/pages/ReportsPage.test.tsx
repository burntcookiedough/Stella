import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
      <ReportsPage />
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
      latest: null,
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

    fireEvent.click(await screen.findByRole("button", { name: /download report/i }));

    expect(
      await screen.findByText(/metrics-only report downloaded because the llm summary was unavailable/i),
    ).toBeTruthy();
  });

  it("shows a failure when report generation fails", async () => {
    downloadReport.mockRejectedValue(new Error("report request failed"));

    renderPage();

    fireEvent.click(await screen.findByRole("button", { name: /download report/i }));

    expect(await screen.findByText(/report request failed/i)).toBeTruthy();
  });
});
