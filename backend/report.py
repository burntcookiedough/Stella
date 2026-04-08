from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fpdf import FPDF
from fpdf.enums import XPos, YPos


class StellaReport(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 10, "Stella v2 Health Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(116, 122, 126)
        self.cell(0, 6, "Local-first health intelligence snapshot", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Generated {datetime.now(UTC).date()} | Page {self.page_no()}", align="C")


def create_health_report(overview: dict[str, Any], correlations: dict[str, Any], ai_analysis: str) -> bytes:
    pdf = StellaReport()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    latest = overview.get("latest") or {}
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, f"User: {overview.get('selected_user', 'n/a')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Latest day: {latest.get('day', 'n/a')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    _section_title(pdf, "Latest Metrics")
    metrics = [
        ("Health score", latest.get("health_score")),
        ("Steps", latest.get("steps")),
        ("Sleep minutes", latest.get("sleep_minutes")),
        ("Resting HR", latest.get("resting_hr")),
        ("HRV", latest.get("hrv")),
    ]
    for label, value in metrics:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(42, 7, f"{label}:", border=0)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, str(value if value is not None else "n/a"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    _section_title(pdf, "Recent Anomalies")
    anomalies = overview.get("anomalies", [])
    if anomalies:
        for anomaly in anomalies[-5:]:
            labels = []
            if anomaly.get("low_sleep"):
                labels.append("low sleep")
            if anomaly.get("low_activity"):
                labels.append("low activity")
            if anomaly.get("high_resting_hr"):
                labels.append("high resting HR")
            pdf.multi_cell(0, 7, f"{anomaly['day']}: {', '.join(labels)}")
    else:
        pdf.cell(0, 7, "No recent anomaly flags.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    _section_title(pdf, "Strongest Correlations")
    pair_rows = correlations.get("pairs", [])[:5]
    if pair_rows:
        for pair in pair_rows:
            descriptor = f"{pair['metric_a']} vs {pair['metric_b']} (lag {pair['lag_days']}d)"
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, descriptor, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(
                0,
                7,
                f"corr={pair['correlation']} across {pair['sample_size']} samples",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
    else:
        pdf.cell(
            0,
            7,
            "Not enough data for correlation analysis yet.",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    _section_title(pdf, "AI Summary")
    pdf.set_font("Helvetica", "", 11)
    safe_text = ai_analysis.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, 7, safe_text)

    return bytes(pdf.output())


def _section_title(pdf: StellaReport, title: str) -> None:
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
