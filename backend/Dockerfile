FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY analytics ./analytics
COPY backend ./backend
COPY llm ./llm
COPY llm_config.yaml .
COPY llm_config.docker.yaml .
COPY llm_config.smoke.yaml .
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
