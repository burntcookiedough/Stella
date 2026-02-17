
from fpdf import FPDF
import datetime

class StellaReport(FPDF):
    def header(self):
        # Title
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Stella Health Analytics - User Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

def create_health_report(user_id, stats, ai_analysis):
    pdf = StellaReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # --- Meta Info ---
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"User ID: {user_id}", 0, 1)
    pdf.cell(0, 10, f"Date: {datetime.date.today()}", 0, 1)
    pdf.ln(5)
    
    # --- Metrics Section ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Daily Metrics", 0, 1)
    pdf.set_font('Arial', '', 12)
    
    metrics = {
        "Health Score": stats.get('health_score', 'N/A'),
        "Steps": stats.get('steps', 'N/A'),
        "Sleep Minutes": stats.get('sleep_minutes', 'N/A'),
        "Trend": stats.get('steps_trend', 'N/A')
    }
    
    for key, val in metrics.items():
        pdf.cell(50, 10, f"{key}:", 0, 0)
        pdf.cell(0, 10, str(val), 0, 1)
    
    pdf.ln(5)
    
    # --- Anomalies Section ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Anomalies Detected", 0, 1)
    pdf.set_font('Arial', '', 12)
    
    anomalies = stats.get('anomalies', {})
    if any(anomalies.values()):
        pdf.set_text_color(255, 0, 0) # Red
        if anomalies.get('low_sleep'):
            pdf.cell(0, 10, "- Low Sleep Detected", 0, 1)
        if anomalies.get('low_steps'):
            pdf.cell(0, 10, "- Low Activity Detected", 0, 1)
        if anomalies.get('high_activity'):
            pdf.cell(0, 10, "- Unusual High Activity", 0, 1)
        pdf.set_text_color(0, 0, 0) # Reset to black
    else:
        pdf.cell(0, 10, "No anomalies detected.", 0, 1)
        
    pdf.ln(5)
    
    # --- AI Analysis Section ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "AI Behavioral Insight", 0, 1)
    pdf.set_font('Arial', '', 11)
    
    # Handle potentially long text
    pdf.multi_cell(0, 7, ai_analysis)
    
    return pdf.output(dest='S').encode('latin-1') # Return bytes
