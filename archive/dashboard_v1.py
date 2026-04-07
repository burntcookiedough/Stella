
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# --- Configuration ---
API_URL = "http://127.0.0.1:8000"
st.set_page_config(
    page_title="Stella",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for "Beautiful Taste" ---
st.markdown("""
    <style>
    /* Global Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;} - Commented out to allow sidebar toggle */

    /* Title Styling */
    .title-text {
        font-size: 3.5rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #a8c0ff, #3f2b96);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle-text {
        font-size: 1.2rem;
        color: #888;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Metric Card Styling */
    .metric-card {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #555;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 600;
        color: #FFF;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #AAA;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-delta {
        font-size: 0.9rem;
        margin-top: 5px;
    }
    .delta-pos { color: #4CAF50; }
    .delta-neg { color: #FF5252; }

    /* Insight Box */
    .insight-box {
        background-color: #252526;
        border-left: 5px solid #a8c0ff;
        padding: 20px;
        border-radius: 5px;
        margin-top: 20px;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def get_users():
    try:
        resp = requests.get(f"{API_URL}/users")
        if resp.status_code == 200:
            return resp.json().get("users", [])
        return []
    except:
        return []

def analyze_user(user_id):
    try:
        resp = requests.post(f"{API_URL}/analyze/{user_id}")
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

# --- Main Layout ---

def chat_with_stella(user_id, message):
    try:
        resp = requests.post(f"{API_URL}/chat", json={"user_id": user_id, "message": message})
        if resp.status_code == 200:
            return resp.json().get("response", "I couldn't process that.")
        return "Backend error."
    except:
        return "Connection failed."

# --- Main Layout ---

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/artificial-intelligence.png", width=80) 
    st.markdown("## Control Panel")
    
    # User Selection
    users = get_users()
    if users:
        selected_user = st.selectbox("Select User ID", users)
    else:
        st.error("Backend offline or no users found.")
        selected_user = None

    analyze_btn = st.button("✨ Analyze Health Data", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("Stella v1.1 | Chat Enabled")

# Main Content
st.markdown('<div class="title-text">Stella</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Privacy-First AI Health Intelligence</div>', unsafe_allow_html=True)

if selected_user:
    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Reset chat if user changes (optional, but good practice)
    if "last_user" not in st.session_state or st.session_state.last_user != selected_user:
        st.session_state.messages = []
        st.session_state.last_user = selected_user

    if analyze_btn:
        with st.spinner("🤖 Stella is analyzing behavioral patterns..."):
            data = analyze_user(selected_user)
            
            if data:
                # Layout: Metrics Row
                col1, col2, col3 = st.columns(3)
                
                metrics = data.get("metrics", {})
                anomalies = data.get("anomalies", {})

                # 1. Health Score
                score = metrics.get('health_score') or 0
                score_color = "#4CAF50" if score > 80 else "#FFC107" if score > 50 else "#FF5252"
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Health Score</div>
                        <div class="metric-value" style="color: {score_color}">{score}</div>
                        <div class="metric-delta">Daily Composite</div>
                    </div>
                    """, unsafe_allow_html=True)

                # 2. Steps
                steps = metrics.get('steps') or 0
                trend = metrics.get('steps_trend', 'stable')
                trend_icon = "↑" if trend == 'increasing' else "↓" if trend == 'decreasing' else "→"
                trend_class = "delta-pos" if trend == 'increasing' else "delta-neg" if trend == 'decreasing' else ""
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Steps (Today)</div>
                        <div class="metric-value">{steps:,}</div>
                        <div class="metric-delta {trend_class}">{trend_icon} {trend.title()}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # 3. Sleep
                sleep_min = metrics.get('sleep_minutes') or 0
                sleep_hrs = sleep_min // 60
                sleep_rem = sleep_min % 60
                sleep_anom = "⚠️ Low Sleep" if anomalies.get('low_sleep') else "Normal"
                sleep_class = "delta-neg" if anomalies.get('low_sleep') else "delta-pos"

                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Sleep Duration</div>
                        <div class="metric-value">{sleep_hrs}h {sleep_rem}m</div>
                        <div class="metric-delta {sleep_class}">{sleep_anom}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # AI Insight Section
                st.markdown("### 🧠 Neural Insight")
                st.markdown(f"""
                <div class="insight-box">
                    {data.get('ai_analysis', 'No analysis generated.').replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

                # Charts Row
                st.markdown("### 📈 Behavioral Trends")
                
                # Placeholder for charts (we would fetch full history in a real app, 
                # here we might just simulate or use what we have if backend supported history)
                # For this demo, let's show a simulated chart or just the single point context
                # To make it "beautiful", we'll create a dummy trend chart using Plotly 
                # (In a real app, we'd fetch the last 30 days data)
                
                # Let's quickly fetch history data for the chart if possible, or just generate a sleek visual
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    # Mock Chart 1: Activity
                    dates = pd.date_range(end=pd.Timestamp.now(), periods=7).strftime("%b %d")
                    values = [max(0, steps + (i*1000 - 3000)) for i in range(7)] # Synthetic curve around current steps
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=dates, y=values, 
                        mode='lines+markers',
                        name='Steps',
                        line=dict(color='#a8c0ff', width=3),
                        fill='tozeroy'
                    ))
                    fig.update_layout(
                        title="7-Day Activity Trend",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#AAA'),
                        height=300,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with chart_col2:
                     # Mock Chart 2: Sleep
                    values_sleep = [max(300, sleep_min + (i*30 - 90)) for i in range(7)]
                    
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(
                        x=dates, y=values_sleep,
                        name='Sleep (min)',
                        marker_color='#3f2b96'
                    ))
                    fig2.update_layout(
                        title="7-Day Sleep Duration",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#AAA'),
                        height=300,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                # --- Report Generation ---
                st.markdown("### 📄 Export")
                if st.button("Generate PDF Report"):
                    with st.spinner("Generating full health report (this may take a moment)..."):
                        try:
                            pdf_resp = requests.get(f"{API_URL}/report/{selected_user}")
                            if pdf_resp.status_code == 200:
                                st.download_button(
                                    label="Download Report",
                                    data=pdf_resp.content,
                                    file_name=f"stella_report_{selected_user}.pdf",
                                    mime="application/pdf"
                                )
                                st.success("Report ready for download!")
                            else:
                                st.error("Failed to generate report.")
                        except Exception as e:
                            st.error(f"Connection error: {e}")

            else:
                st.error("Failed to fetch analysis. Ensure Backend is running.")

    # --- Chat Interface ---
    st.markdown("---")
    st.markdown("### 💬 Ask Stella")

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about your health metrics..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response from Stella
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            with requests.post(f"{API_URL}/chat", json={"user_id": selected_user, "message": prompt}, stream=True) as r:
                for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        # Add assistant message to history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

else:
    # Empty State
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; color: #555;">
        <h3>👈 Select a user and click Analyze to begin</h3>
        <p>Stella needs a target profile to generate insights.</p>
    </div>
    """, unsafe_allow_html=True)
