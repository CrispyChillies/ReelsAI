# PowerShell script to set EB environment variables from file
# Usage: .\set_eb_env.ps1

$envVarsFile = ".env.production"

if (-Not (Test-Path $envVarsFile)) {
    Write-Error "File $envVarsFile not found!"
    exit 1
}

Write-Host "Reading environment variables from $envVarsFile..." -ForegroundColor Green

# Read file and filter out comments and empty lines
$envVars = Get-Content $envVarsFile | 
    Where-Object { $_ -match '\S' -and $_ -notmatch '^\s*#' } |
    ForEach-Object { $_.Trim() }

if ($envVars.Count -eq 0) {
    Write-Error "No valid environment variables found in $envVarsFile"
    exit 1
}

Write-Host "Found $($envVars.Count) environment variables" -ForegroundColor Cyan

# Join all variables and pass to eb setenv
$envString = $envVars -join ' '

Write-Host "`nSetting environment variables..." -ForegroundColor Yellow
Write-Host "Running: eb setenv $envString" -ForegroundColor Gray

# Execute the command
Invoke-Expression "eb setenv $envString"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n Success! Environment variables set successfully!" -ForegroundColor Green
} else {
    Write-Error "Failed to set environment variables"
    exit $LASTEXITCODE
}
