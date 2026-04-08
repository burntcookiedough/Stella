$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host "[Stella] $message" -ForegroundColor Cyan
}

function Write-Warn($message) {
    Write-Host "[Stella] $message" -ForegroundColor Yellow
}

function Test-PortOpen([int]$Port) {
    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $connected = $iar.AsyncWaitHandle.WaitOne(250)
        if (-not $connected) {
            $client.Close()
            return $false
        }
        $client.EndConnect($iar)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $PSScriptRoot
    )

    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed: $FilePath $($Arguments -join ' ')"
        }
    } finally {
        Pop-Location
    }
}

function Wait-ForHttp {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$TimeoutSeconds = 90
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 800
        }
    }
    return $false
}

function Get-ConfiguredOllamaModel {
    if ($env:STELLA_LLM_CONFIG) {
        $configPath = $env:STELLA_LLM_CONFIG
    } else {
        $runtimeRoot = if ($env:STELLA_BASE_DIR) {
            $env:STELLA_BASE_DIR
        } elseif ($env:LOCALAPPDATA) {
            Join-Path $env:LOCALAPPDATA "Stella"
        } else {
            Join-Path $PSScriptRoot ".stella-runtime"
        }

        $runtimeConfig = Join-Path $runtimeRoot "llm_config.yaml"
        $configPath = if (Test-Path $runtimeConfig) { $runtimeConfig } else { Join-Path $PSScriptRoot "llm_config.yaml" }
    }

    if (-not (Test-Path $configPath)) {
        return "mistral"
    }

    foreach ($line in Get-Content $configPath) {
        if ($line -match "^\s*model\s*:\s*(.+?)\s*$") {
            return ($Matches[1].Trim() -replace "^[`"']|[`"']$", "")
        }
    }

    return "mistral"
}

function Get-ShellExecutable {
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($pwsh) {
        return $pwsh.Source
    }
    return "powershell"
}

function Ensure-PythonDeps {
    Write-Step "Checking Python dependencies"
    & python -c "import fastapi, uvicorn, httpx, duckdb" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Step "Installing Python dependencies"
        Invoke-CheckedCommand -FilePath "python" -Arguments @("-m", "pip", "install", "-r", "requirements.txt")
    }
}

function Ensure-NodeDeps {
    Write-Step "Checking frontend dependencies"
    if (-not (Test-Path "frontend\node_modules")) {
        Write-Step "Installing frontend dependencies"
        $installArgs = if (Test-Path "frontend\package-lock.json") {
            @("ci")
        } else {
            @("install")
        }
        Invoke-CheckedCommand -FilePath "npm" -Arguments $installArgs -WorkingDirectory (Join-Path $PSScriptRoot "frontend")
    }
}

function Ensure-OllamaModel {
    if ($env:STELLA_SKIP_OLLAMA -eq "1") {
        Write-Warn "Skipping Ollama checks because STELLA_SKIP_OLLAMA=1"
        return
    }

    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        Write-Warn "Ollama CLI not found. Chat and AI report summaries may be unavailable."
        return
    }

    $model = Get-ConfiguredOllamaModel
    Write-Step "Checking Ollama model availability"
    $models = & ollama list 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Could not query Ollama. Start the Ollama app if you want live chat and AI summaries."
        return
    }

    if ($models -notmatch [regex]::Escape($model)) {
        Write-Step "Pulling $model"
        Invoke-CheckedCommand -FilePath "ollama" -Arguments @("pull", $model)
    }
}

function Start-Backend {
    if (Test-PortOpen 8000) {
        Write-Step "Backend already running on port 8000"
        return
    }

    Write-Step "Starting backend on http://127.0.0.1:8000"
    $shell = Get-ShellExecutable
    Start-Process $shell -WorkingDirectory $PSScriptRoot -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$PSScriptRoot'; python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
    ) | Out-Null
}

function Start-Frontend {
    if (Test-PortOpen 5173) {
        Write-Step "Frontend already running on port 5173"
        return
    }

    Write-Step "Starting frontend on http://127.0.0.1:5173"
    $shell = Get-ShellExecutable
    $frontendDir = Join-Path $PSScriptRoot "frontend"
    Start-Process $shell -WorkingDirectory $frontendDir -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$frontendDir'; npm run dev -- --host 127.0.0.1 --port 5173"
    ) | Out-Null
}

Set-Location $PSScriptRoot

Write-Host "===================================================" -ForegroundColor DarkCyan
Write-Host "          STELLA - Local Product Launcher          " -ForegroundColor White
Write-Host "===================================================" -ForegroundColor DarkCyan

Ensure-PythonDeps
Ensure-NodeDeps
Ensure-OllamaModel
Start-Backend
if (-not (Wait-ForHttp -Url "http://127.0.0.1:8000/readyz")) {
    throw "Backend did not become ready on http://127.0.0.1:8000/readyz"
}
Start-Frontend
if (-not (Wait-ForHttp -Url "http://127.0.0.1:5173")) {
    throw "Frontend did not become ready on http://127.0.0.1:5173"
}

Write-Step "Opening Stella in your browser"
Start-Process "http://127.0.0.1:5173"

Write-Host ""
Write-Host "Stella is starting." -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend docs: http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "Close the server windows when you want to stop the app." -ForegroundColor Yellow
Read-Host "Press Enter to close this launcher"
