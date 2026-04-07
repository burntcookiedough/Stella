import { useDeferredValue, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Plot from "react-plotly.js";

import { fetchCorrelations } from "../api/client";

export function AnalyticsPage() {
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const { data, isLoading } = useQuery({
    queryKey: ["correlations"],
    queryFn: () => fetchCorrelations(),
  });

  if (isLoading) {
    return <p className="status">Loading correlations...</p>;
  }

  const pairs = (data?.pairs ?? []).filter((pair) => {
    const query = deferredSearch.toLowerCase();
    return !query || `${pair.metric_a} ${pair.metric_b}`.toLowerCase().includes(query);
  });

  const matrix = data?.matrix ?? {};
  const labels = Object.keys(matrix);
  const heatmap = labels.map((rowLabel) =>
    labels.map((columnLabel) => matrix[rowLabel]?.[columnLabel] ?? (rowLabel === columnLabel ? 1 : 0)),
  );

  return (
    <div className="page-grid analytics-grid">
      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Correlation matrix</p>
          <h3>Metric relationships</h3>
        </div>
        <div className="plot-shell">
          <Plot
            data={[
              {
                z: heatmap,
                x: labels,
                y: labels,
                type: "heatmap",
                colorscale: [
                  [0, "#122025"],
                  [0.5, "#2f6c7a"],
                  [1, "#8df0c6"],
                ],
              },
            ]}
            layout={{
              paper_bgcolor: "transparent",
              plot_bgcolor: "transparent",
              font: { color: "#d5dddd" },
              margin: { l: 40, r: 20, t: 20, b: 40 },
            }}
            style={{ width: "100%", height: "100%" }}
            config={{ displayModeBar: false, responsive: true }}
          />
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Pair details</p>
          <h3>Strongest signals</h3>
        </div>
        <input
          className="filter-input"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Filter by metric"
        />
        <div className="list-block">
          {pairs.map((pair) => (
            <div key={`${pair.metric_a}-${pair.metric_b}-${pair.lag_days}`} className="list-row stacked">
              <strong>
                {pair.metric_a} vs {pair.metric_b}
              </strong>
              <span>
                corr {pair.correlation} | lag {pair.lag_days}d | n={pair.sample_size}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
