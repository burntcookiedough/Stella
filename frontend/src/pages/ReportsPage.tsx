import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { downloadReport, fetchOverview } from "../api/client";

export function ReportsPage() {
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
        <button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
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
