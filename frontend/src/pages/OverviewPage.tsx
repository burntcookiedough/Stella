import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { fetchOverview } from "../api/client";

export function OverviewPage() {
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
