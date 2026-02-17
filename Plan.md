

# PROJECT TITLE

**Stella – AI-Powered Wearable Health Analytics Dashboard**

---

# 1️⃣ What Are We Going to Do?

We are building a **full-stack AI health analytics product** that:

1. Uses a clean wearable dataset (Fitbit)
2. Processes time-series data
3. Extracts behavioral health trends
4. Computes anomaly & risk signals
5. Converts structured insights into natural-language explanations using a locally deployed LLM
6. Presents everything in a professional dashboard
7. Deploys frontend/backend for free
8. Runs LLM locally on GPU (no API dependency)

This is not a chatbot.

This is a structured analytics + AI interpretation system.

---

# 2️⃣ What Problem Are We Solving?

Raw wearable data is:

* Numeric
* Hard to interpret
* Behaviorally noisy
* Insight-poor for normal users

We solve:

> “How do I convert wearable time-series data into meaningful, structured, actionable insights — without hallucinating medical advice?”

We build a controlled LLM interpretation layer on top of deterministic analytics.

That’s the differentiator.

---

# 3️⃣ How Are We Going to Achieve It?

We split the system into 6 core layers.

---

# LAYER 1 — Dataset

We use:

Fitbit Fitness Tracker Data

Why:

* Clean CSV
* Daily metrics
* Easy aggregation
* No XML parsing nightmare

Key tables:

* dailyActivity_merged.csv
* sleepDay_merged.csv

---

# LAYER 2 — Data Engineering Pipeline

We:

1. Load CSV using pandas
2. Merge by date
3. Convert timestamps
4. Aggregate daily metrics
5. Handle missing values
6. Standardize units

Output:

| date | steps | sleep_hours | calories | resting_hr | hrv |

This becomes our base dataset.

---

# LAYER 3 — Feature Engineering

We compute meaningful health signals.

Core metrics:

* 7-day rolling average
* % change week-over-week
* Sleep debt
* Activity variance
* Resting HR drift
* HRV drop %
* Activity consistency score

We transform raw logs into structured indicators.

This is the real intelligence layer.

---

# LAYER 4 — Risk & Anomaly Engine

We implement:

### 1. Z-score anomaly detection

Flags unusual deviations.

### 2. Weighted risk score model

Example:

risk_score =
0.4 * normalized_sleep_drop

* 0.3 * normalized_hr_increase
* 0.3 * normalized_activity_drop

Outputs:

* Risk score (0–1)
* Risk level (Low / Moderate / High)

This layer is deterministic and explainable.

No black box.

---

# LAYER 5 — Structured Insight JSON

We never send raw tables to the LLM.

We create a clean structured summary:

```json
{
  "sleep_change_percent": -15,
  "resting_hr_change_percent": 6,
  "activity_change_percent": -12,
  "risk_score": 0.72,
  "risk_level": "moderate"
}
```

LLM becomes interpreter, not analyst.

This design prevents hallucinations.

---

# LAYER 6 — LLM Explanation Engine

We use:

Mistral 7B

Running locally via:

Ollama

On local hardware (CPU or GPU).

Configuration:

* 4-bit quantized
* Temperature = 0.2
* Structured prompt template
* Guardrail output filter

Prompt example:

```
Interpret structured wearable health trend data.
Do not provide medical diagnosis.
Do not mention diseases.
Focus only on behavioral insights and lifestyle suggestions.
Explain risk level clearly.
```

---

# 4️⃣ Work Process (Execution Timeline)

We break it into disciplined phases.

---

## PHASE 1 — Local LLM Setup

* Install Ollama
* Pull mistral model
* Verify GPU usage
* Benchmark response time

Goal:
Stable local inference pipeline.

---

## PHASE 2 — Data + Analytics Module

* Implement CSV ingestion
* Create feature engineering functions
* Implement anomaly scoring
* Validate outputs on sample users

Goal:
Stable structured JSON output.

---

## PHASE 3 — Backend API

Using:

FastAPI

Endpoints:

POST /analyze
GET /summary

Backend responsibilities:

* Load processed data
* Generate structured JSON
* Call Ollama API
* Apply guardrail filter
* Return final response

---

## PHASE 4 — Frontend Dashboard

Using:

Streamlit

Dashboard Components:

1. Metric cards
2. Line graphs (steps, sleep, HR)
3. Risk score indicator
4. AI explanation panel

UX goal:
Clean, SaaS-like, no clutter.

---

## PHASE 5 — Packaging & Demo

Goal:
One-click local launch.

We create:
`run_stella.bat` (or .sh) that:
1. Starts Ollama
2. Starts Backend (FastAPI)
3. Starts Frontend (Streamlit)

No cloud hosting. 
Total data privacy.
100% offline capability.

---

# 5️⃣ Final System Setup

Here is the final production structure:

```
Stella/
│
├── data/
│   ├── raw/
│   ├── processed/
│
├── analytics/
│   ├── feature_engineering.py
│   ├── anomaly_engine.py
│
├── llm/
│   ├── prompt_template.py
│   ├── guardrail_filter.py
│
├── backend/
│   ├── main.py  (FastAPI)
│
├── frontend/
│   ├── dashboard.py  (Streamlit)
│
├── requirements.txt
└── README.md
```

Clean separation of concerns.

---

# 6️⃣ Hallucination Prevention Strategy

We combine:

1. Structured JSON input
2. Low temperature inference
3. Strict system prompt
4. Regex-based post-processing filter
5. UI disclaimer

This is professional-grade control.

---

# 7️⃣ What This Demonstrates Technically

You demonstrate:

* Time-series feature engineering
* Risk scoring logic
* Explainable AI design
* LLM guardrail architecture
* Local quantized inference on GPU
* API design
* Frontend product deployment
* Free-tier hosting strategy

This is far beyond “I used GPT.”

---

# 8️⃣ Final Product Experience

User flow:

1. Upload dataset
2. Dashboard loads
3. Trends visualized
4. Risk score calculated
5. AI explanation generated
6. Behavioral suggestions displayed

Feels like SaaS.
Runs locally.
Free.
Scalable.

---


