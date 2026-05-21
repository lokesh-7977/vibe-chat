$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

if (Test-Path ".env") {
  Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $parts = $line.Split("=", 2)
    if ($parts.Length -ne 2) { return }
    $name = $parts[0].Trim()
    $value = $parts[1].Trim().Trim("'").Trim('"')
    if ($name) { Set-Item -Path "Env:$name" -Value $value }
  }
}

if (-not $env:DATABASE_URL) {
  throw "DATABASE_URL not set. Add it to .env or set `$env:DATABASE_URL before running."
}

if (Test-Path ".\\.venv\\Scripts\\python.exe") {
  & ".\\.venv\\Scripts\\python.exe" -m alembic upgrade head
} else {
  python -m alembic upgrade head
}

