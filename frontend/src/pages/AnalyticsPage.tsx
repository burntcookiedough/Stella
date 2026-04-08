import { Fragment, useDeferredValue, useState } from "react";
import { useQuery } from "@tanstack/react-query";

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
        {labels.length ? (
          <div
            className="matrix-grid"
            style={{ gridTemplateColumns: `minmax(140px, 1.4fr) repeat(${labels.length}, minmax(72px, 1fr))` }}
          >
            <div className="matrix-corner">Metric</div>
            {labels.map((label) => (
              <div key={`column-${label}`} className="matrix-axis">
                {label}
              </div>
            ))}
            {labels.map((rowLabel, rowIndex) => (
              <Fragment key={rowLabel}>
                <div className="matrix-axis matrix-axis-row">{rowLabel}</div>
                {heatmap[rowIndex].map((value, columnIndex) => (
                  <div
                    key={`${rowLabel}-${labels[columnIndex]}`}
                    className="matrix-cell"
                    style={{ background: correlationColor(value) }}
                    title={`${rowLabel} vs ${labels[columnIndex]}: ${value.toFixed(3)}`}
                  >
                    {value.toFixed(2)}
                  </div>
                ))}
              </Fragment>
            ))}
          </div>
        ) : (
          <p className="muted-copy">Correlation pairs will appear after Stella has enough imported history.</p>
        )}
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

function correlationColor(value: number): string {
  const normalized = Math.max(-1, Math.min(1, value));
  if (normalized >= 0) {
    const alpha = 0.18 + normalized * 0.42;
    return `rgba(123, 219, 192, ${alpha.toFixed(3)})`;
  }
  const alpha = 0.14 + Math.abs(normalized) * 0.34;
  return `rgba(121, 184, 255, ${alpha.toFixed(3)})`;
}
