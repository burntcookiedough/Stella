import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { fetchOverview, type ReadyStateResponse } from "../api/client";

export function OverviewPage({ runtime }: { runtime?: ReadyStateResponse }) {
  const { data, isLoading } = useQuery({
    queryKey: ["overview"],
    queryFn: () => fetchOverview(),
  });

  if (isLoading) {
    return <p className="status">Loading overview...</p>;
  }

  const latest = data?.latest;
  const trendData = data?.trend_slices ?? [];
  const anomalies = data?.anomalies ?? [];

  if ((runtime && !runtime.has_data) || (!latest && trendData.length === 0)) {
    return (
      <section className="panel empty-state-panel">
        <div className="panel-heading">
          <p className="eyebrow">First run</p>
          <h3>Stella is ready for your first import</h3>
        </div>
        <p className="muted-copy">
          This workspace starts empty on purpose. Import a Fitbit, Apple Health, Google Takeout, Oura, Garmin, or
          manual CSV export to generate your first overview.
        </p>
        <div className="empty-state-grid">
          <div className="empty-state-card">
            <p className="control-label">1. Gather your export files</p>
            <p className="status">Choose the raw files exactly as they came from the provider export bundle.</p>
          </div>
          <div className="empty-state-card">
            <p className="control-label">2. Run the first import</p>
            <p className="status">Use the import panel in the workspace header to ingest the files into Stella.</p>
          </div>
          <div className="empty-state-card">
            <p className="control-label">3. Review analytics</p>
            <p className="status">After import, Stella will unlock overview charts, reports, and deeper analytics.</p>
          </div>
          <div className="empty-state-card">
            <p className="control-label">AI runtime</p>
            <p className="status">
              {!runtime
                ? "Runtime health is still loading."
                : runtime.llm_reachable
                ? `LLM ready with ${runtime.llm_provider} / ${runtime.llm_model}.`
                : "Metrics-only mode is expected until the optional model runtime is available."}
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <div className="page-grid">
      <section className="metric-rail">
        <Metric label="Health score" value={latest?.health_score ?? "n/a"} />
        <Metric label="Steps" value={latest?.steps ?? "n/a"} />
        <Metric label="Sleep minutes" value={latest?.sleep_minutes ?? "n/a"} />
        <Metric label="Resting HR" value={latest?.resting_hr ?? "n/a"} />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Trend slice</p>
          <h3>Last 21 days</h3>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="stepsFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8df0c6" stopOpacity={0.42} />
                  <stop offset="100%" stopColor="#8df0c6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis dataKey="day" stroke="#758085" tickLine={false} axisLine={false} />
              <YAxis stroke="#758085" tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{
                  background: "#111818",
                  border: "1px solid rgba(141,240,198,0.18)",
                  borderRadius: 16,
                }}
              />
              <Area type="monotone" dataKey="steps" stroke="#8df0c6" fill="url(#stepsFill)" strokeWidth={2} />
              <Area type="monotone" dataKey="sleep_minutes" stroke="#5ca7ff" fill="transparent" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">Recent anomalies</p>
          <h3>Last 14 days</h3>
        </div>
        <div className="list-block">
          {anomalies.length ? (
            anomalies.map((item) => (
              <div key={item.day} className="list-row">
                <span>{item.day}</span>
                <span>
                  {item.low_sleep ? "sleep " : ""}
                  {item.low_activity ? "activity " : ""}
                  {item.high_resting_hr ? "resting HR" : ""}
                </span>
              </div>
            ))
          ) : (
            <p className="muted-copy">No active anomaly flags in the recent window.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric-row">
      <p>{label}</p>
      <strong>{value}</strong>
    </div>
  );
}
