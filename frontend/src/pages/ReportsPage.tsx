import { useMutation, useQuery } from "@tanstack/react-query";

import { downloadReport, fetchOverview } from "../api/client";

export function ReportsPage() {
  const { data } = useQuery({
    queryKey: ["overview"],
    queryFn: () => fetchOverview(),
  });

  const mutation = useMutation({
    mutationFn: () => downloadReport(data?.selected_user ?? undefined),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `stella-report-${data?.selected_user ?? "latest"}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    },
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
        {mutation.error ? <p className="status error">{String(mutation.error)}</p> : null}
      </div>
    </section>
  );
}
