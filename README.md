# Stella

**Privacy-First AI Health Analytics**

Stella is a local, full-stack health analytics platform that processes wearable data (Fitbit) and uses a local LLM (Mistral via Ollama) to generate behavioral insights without sending data to the cloud.

---

## 🚀 Quick Start (Windows)

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Ensure Ollama is Running**
    -   Download from [ollama.com](https://ollama.com).
    -   Run `ollama pull mistral` in your terminal.

3.  **Launch Stella**
    Double-click `run_stella.bat`
    (Or run `./run_stella.bat` in terminal)

    This will start:
    -   Backend API: `http://127.0.0.1:8000`
    -   Frontend Dashboard: `http://localhost:8501`

---

## 📂 Project Structure

```
Stella/
├── analytics/          # Data processing pipeline
│   ├── ingest.py       # CSV loading & merging
│   ├── features.py     # Rolling averages & Z-scores
│   └── anomaly.py      # Statistical anomaly detection
├── backend/            # FastAPI Server
│   └── main.py         # API Endpoints & Logic
├── frontend/           # Streamlit Dashboard
│   └── dashboard.py    # UI & Visualization
├── llm/                # AI Engine
│   └── engine.py       # Ollama Integration
├── data/               # Local Data Storage
└── run_stella.bat      # One-click Launcher
```

## 🛠 Tech Stack

-   **Frontend**: Streamlit (Python)
-   **Backend**: FastAPI (Python)
-   **AI Engine**: Ollama (Mistral 7B)
-   **Data**: Pandas, Plotly

## 💬 New Feature: Interactive Chat
You can now ask Stella questions about the data!
- "Why is my sleep score low?"
- "How do I compare to last week?"
- "Give me a summary of my anomalies."

## 🔒 Privacy Note

All data processing happens locally on your machine. No health data is uploaded to any external server.
