@echo off
title Stella Launcher
echo ===================================================
echo       STELLA - Local AI Health Analytics
echo ===================================================
echo.

:: 1. Check for Ollama CLI
echo [*] Checking Ollama Status...
set OLLAMA_FOUND=0
where ollama >nul 2>nul
if %errorlevel% equ 0 (
    echo [^V] Ollama CLI found.
    set OLLAMA_FOUND=1
) else (
    echo [!] Ollama CLI not found in PATH.
    echo     Assuming Ollama service is running in background...
    echo     (Skipping model check. If backend fails, ensure 'mistral:latest' is pulled)
)

:: 2. Check/Pull Model (Only if CLI is available)
if %OLLAMA_FOUND% equ 1 (
    echo.
    echo [*] Checking for Mistral model...
    ollama list | findstr "mistral" >nul
    if %errorlevel% neq 0 (
        echo [!] Mistral model not found. Pulling now...
        ollama pull mistral:latest
    ) else (
        echo [^V] Mistral model found.
    )
)

:: 3. Start Backend
echo.
echo [*] Starting Backend API (FastAPI)...
start "Stella Backend" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

:: Wait for backend to initialize
echo     Waiting 5 seconds for backend to start...
timeout /t 5 >nul

:: 4. Start Frontend
echo.
echo [*] Starting Frontend Dashboard (Streamlit)...
start "Stella Dashboard" cmd /k "python -m streamlit run frontend/dashboard.py"

echo.
echo [^V] System Launched!
echo     - API: http://127.0.0.1:8000/docs
echo     - Dashboard: http://localhost:8501
echo.
echo Press any key to exit this launcher (Servers will keep running).
pause
