$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host "[Stella Docker] $message" -ForegroundColor Cyan
}

function Wait-ForHttp {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$TimeoutSeconds = 180
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Milliseconds 1000
        }
    }

    return $false
}

Set-Location $PSScriptRoot

$profileArgs = @()
if ($env:STELLA_DOCKER_WITH_OLLAMA -eq "1") {
    $profileArgs = @("--profile", "local-llm")
}

Write-Step "Building and starting the Docker stack"
docker compose @profileArgs up -d --build
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up failed."
}

Write-Step "Waiting for backend readiness"
if (-not (Wait-ForHttp -Url "http://127.0.0.1:8000/readyz")) {
    throw "Backend did not become ready on http://127.0.0.1:8000/readyz"
}

Write-Step "Waiting for frontend readiness"
if (-not (Wait-ForHttp -Url "http://127.0.0.1:5173")) {
    throw "Frontend did not become ready on http://127.0.0.1:5173"
}

Write-Step "Opening Stella in your browser"
Start-Process "http://127.0.0.1:5173"

Write-Host ""
Write-Host "Docker stack is running." -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend docs: http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "Use 'docker compose down' to stop the stack." -ForegroundColor Yellow
Read-Host "Press Enter to close this launcher"
