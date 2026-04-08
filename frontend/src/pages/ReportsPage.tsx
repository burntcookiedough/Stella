import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { downloadReport, fetchOverview, type ReadyStateResponse } from "../api/client";

export function ReportsPage({
  runtime,
  runtimeError,
}: {
  runtime?: ReadyStateResponse;
  runtimeError?: Error | null;
}) {
  const [reportStatus, setReportStatus] = useState<{ tone: "ok" | "warning"; message: string } | null>(null);
  const { data } = useQuery({
    queryKey: ["overview"],
    queryFn: () => fetchOverview(),
  });

  const mutation = useMutation({
    onMutate: () => setReportStatus(null),
    mutationFn: () => downloadReport(data?.selected_user ?? undefined),
    onSuccess: (download) => {
      const url = URL.createObjectURL(download.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = download.fileName;
      link.click();
      URL.revokeObjectURL(url);
      if (download.llmStatus === "fallback") {
        setReportStatus({
          tone: "warning",
          message: download.llmError
            ? `Metrics-only report downloaded because the LLM summary was unavailable: ${download.llmError}`
            : "Metrics-only report downloaded because the LLM summary was unavailable.",
        });
        return;
      }
      setReportStatus({ tone: "ok", message: "Report downloaded successfully." });
    },
    onError: () => setReportStatus(null),
  });

  if (runtime && !runtime.has_data) {
    return (
      <section className="page-grid">
        <div className="panel empty-state-panel">
          <div className="panel-heading">
            <p className="eyebrow">PDF report</p>
            <h3>Import data before generating a report</h3>
          </div>
          <p className="muted-copy">
            Stella only generates reports from imported health data. Run your first import from the workspace header,
            then come back here to download a portable summary.
          </p>
        </div>
      </section>
    );
  }

  const disabled = Boolean(runtimeError) || !data?.latest;

  return (
    <section className="page-grid">
      <div className="panel">
        <div className="panel-heading">
          <p className="eyebrow">PDF report</p>
          <h3>Generate a portable health summary</h3>
        </div>
        <p className="muted-copy">
          The report packages the latest KPIs, anomaly window, top correlations, and an LLM summary
          into a single PDF snapshot.
        </p>
        {runtime && !runtime.llm_reachable ? (
          <p className="status warning">
            Metrics-only reports are expected right now. Stella will still generate the PDF even while the model runtime
            is unavailable.
          </p>
        ) : null}
        {!data?.latest ? (
          <p className="status warning">No reportable overview is available yet. Import data before requesting a PDF.</p>
        ) : null}
        {runtimeError ? (
          <p className="status error">The backend runtime is offline. Restart Stella before requesting a report.</p>
        ) : null}
        <button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending || disabled}>
          {mutation.isPending ? "Rendering..." : "Download report"}
        </button>
        {reportStatus ? (
          <p className={`status ${reportStatus.tone === "warning" ? "warning" : ""}`}>{reportStatus.message}</p>
        ) : null}
        {mutation.error ? <p className="status error">{String(mutation.error)}</p> : null}
      </div>
    </section>
  );
}
