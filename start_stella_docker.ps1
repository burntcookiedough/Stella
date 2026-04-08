$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host "[Stella Docker] $message" -ForegroundColor Cyan
}

function Write-Warn($message) {
    Write-Host "[Stella Docker] $message" -ForegroundColor Yellow
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

function Test-CommandAvailable {
    param([Parameter(Mandatory = $true)][string]$Name)

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-SecureRandomString {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Length,
        [Parameter(Mandatory = $true)]
        [string]$Alphabet
    )

    $bytes = [byte[]]::new($Length)
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $builder = [System.Text.StringBuilder]::new()
    for ($index = 0; $index -lt $Length; $index++) {
        [void]$builder.Append($Alphabet[$bytes[$index] % $Alphabet.Length])
    }
    return $builder.ToString()
}

function Get-EnvFileMap {
    param([Parameter(Mandatory = $true)][string]$Path)

    $map = @{}
    if (-not (Test-Path $Path)) {
        return $map
    }

    foreach ($line in Get-Content $Path) {
        if ($line -match '^\s*#' -or $line -notmatch '=') {
            continue
        }
        $key, $value = $line.Split('=', 2)
        $map[$key.Trim()] = $value.Trim()
    }
    return $map
}

function Set-EnvFileValues {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][hashtable]$Values
    )

    $lines = [System.Collections.Generic.List[string]]::new()
    if (Test-Path $Path) {
        foreach ($line in Get-Content $Path) {
            $lines.Add($line)
        }
    }

    foreach ($key in $Values.Keys) {
        $updated = $false
        for ($index = 0; $index -lt $lines.Count; $index++) {
            if ($lines[$index] -match "^\s*$([regex]::Escape($key))=") {
                $lines[$index] = "$key=$($Values[$key])"
                $updated = $true
                break
            }
        }
        if (-not $updated) {
            $lines.Add("$key=$($Values[$key])")
        }
    }

    Set-Content -Path $Path -Value $lines
}

function Test-WeakDockerValue {
    param(
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $normalized = $Value.Trim().ToLowerInvariant()
    switch ($Key) {
        "STELLA_USERNAME" {
            return $normalized -ne "stella"
        }
        "STELLA_PASSWORD" {
            return ($normalized -in @("", "stella", "password", "replace-me", "generated_at_first_run")) -or $Value.Trim().Length -lt 12
        }
        "STELLA_JWT_SECRET" {
            return ($normalized -in @("", "replace-me", "change-me-in-production", "generated_at_first_run")) -or $Value.Trim().Length -lt 32
        }
        default {
            return [string]::IsNullOrWhiteSpace($Value)
        }
    }
}

function Ensure-DockerPrereqs {
    if (-not (Test-CommandAvailable "docker")) {
        throw "Docker CLI was not found. Install Docker Desktop, then re-run run_stella_docker.bat."
    }

    Write-Step "Checking Docker Desktop availability"
    & docker compose version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose is unavailable. Open Docker Desktop and wait for it to finish starting."
    }

    & docker info | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Desktop is installed but the engine is not reachable. Start Docker Desktop, then try again."
    }
}

function Ensure-DockerEnv {
    $envPath = Join-Path $PSScriptRoot ".env"
    $templatePath = Join-Path $PSScriptRoot ".env.example"
    $created = $false

    if (-not (Test-Path $templatePath)) {
        throw "Missing .env.example. The Docker launcher cannot bootstrap configuration."
    }

    if (-not (Test-Path $envPath)) {
        Write-Step "Creating .env from .env.example"
        Copy-Item $templatePath $envPath
        $created = $true
        Set-EnvFileValues -Path $envPath -Values @{
            STELLA_USERNAME = "stella"
            STELLA_PASSWORD = (Get-SecureRandomString -Length 20 -Alphabet "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789")
            STELLA_JWT_SECRET = (Get-SecureRandomString -Length 48 -Alphabet "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        }
    }

    $values = Get-EnvFileMap -Path $envPath
    foreach ($requiredKey in @("STELLA_FRONTEND_ORIGIN", "STELLA_USERNAME", "STELLA_PASSWORD", "STELLA_JWT_SECRET")) {
        if (-not $values.ContainsKey($requiredKey) -or [string]::IsNullOrWhiteSpace($values[$requiredKey])) {
            throw "The Docker config at $envPath is missing $requiredKey. Delete .env to regenerate it, or add the value manually."
        }
        if (Test-WeakDockerValue -Key $requiredKey -Value $values[$requiredKey]) {
            throw "The Docker config at $envPath still contains a weak or placeholder value for $requiredKey. Delete .env to regenerate it, or replace the value manually."
        }
    }

    return @{
        Path = $envPath
        Values = $values
        Created = $created
    }
}

Set-Location $PSScriptRoot

$profileArgs = @()
if ($env:STELLA_DOCKER_WITH_OLLAMA -eq "1") {
    $profileArgs = @("--profile", "local-llm")
}

Ensure-DockerPrereqs
$dockerEnv = Ensure-DockerEnv

Write-Step "Building and starting the Docker stack"
& docker compose @profileArgs up -d --build
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up failed."
}

Write-Step "Waiting for backend readiness"
if (-not (Wait-ForHttp -Url "http://127.0.0.1:8000/readyz")) {
    throw "Backend did not become ready on http://127.0.0.1:8000/readyz"
}

Write-Step "Waiting for packaged frontend readiness"
if (-not (Wait-ForHttp -Url "http://127.0.0.1:5173")) {
    throw "Frontend did not become ready on http://127.0.0.1:5173"
}

Write-Step "Opening Stella in your browser"
Start-Process "http://127.0.0.1:5173"

Write-Host ""
Write-Host "Docker stack is running." -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend docs: http://127.0.0.1:8000/docs"
Write-Host "Runtime volume: stella-runtime"
Write-Host ".env path: $($dockerEnv.Path)"
Write-Host "Username: $($dockerEnv.Values.STELLA_USERNAME)"
if ($dockerEnv.Created) {
    Write-Host "Password: $($dockerEnv.Values.STELLA_PASSWORD)" -ForegroundColor Yellow
} else {
    Write-Warn "Password is stored in .env. Open that file if you need to recover it."
}
Write-Host ""
if ($env:STELLA_DOCKER_WITH_OLLAMA -eq "1") {
    Write-Host "LLM mode: local-llm profile enabled" -ForegroundColor Green
} else {
    Write-Warn "LLM mode: metrics-only by default. Set STELLA_DOCKER_WITH_OLLAMA=1 if you want Ollama sidecar support."
}
Write-Host "Use 'docker compose down' to stop the stack." -ForegroundColor Yellow
Read-Host "Press Enter to close this launcher"
