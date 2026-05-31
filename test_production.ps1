# Quick Setup & Test Script

Write-Host "Production Voice Agent - Setup & Test" -ForegroundColor Cyan
Write-Host "=" -NoNewline; Write-Host ("=" * 69)

# Check OpenAI API key
if (!(Test-Path ".env")) {
    Write-Host "`n✗ .env file not found" -ForegroundColor Red
    exit
}

$envContent = Get-Content ".env"
if (!($envContent -match "OPENAI_API_KEY=(.+)")) {
    Write-Host "✗ OPENAI_API_KEY not set in .env" -ForegroundColor Red
    exit
}

if (!($envContent -match "CARTESIA_API_KEY=(.+)")) {
    Write-Host "✗ CARTESIA_API_KEY not set in .env" -ForegroundColor Red
    exit
}

Write-Host "`n✓ API keys found" -ForegroundColor Green

# Check/Install dependencies
Write-Host "`n🔄 Checking dependencies..." -ForegroundColor Yellow

$packages = @("openai", "whisper", "torch", "noisereduce", "speech_recognition", "pygame", "pydantic", "fpdf2")
$missing = @()

foreach ($pkg in $packages) {
    $pkgName = $pkg.Replace("_", "-")
    $importName = if ($pkg -eq "fpdf2") { "fpdf" } else { $pkg }
    $check = python -c "import $($importName); print('OK')" 2>$null
    if ($check -eq "OK") {
        Write-Host "  ✓ $pkgName" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $pkgName" -ForegroundColor Red
        $missing += $pkgName
    }
}

if ($missing.Count -gt 0) {
    Write-Host "`n⚠ Missing packages. Install? (y/n)" -ForegroundColor Yellow
    $install = Read-Host
    if ($install -eq "y") {
        Write-Host "`nInstalling..." -ForegroundColor Cyan
        pip install -r requirements.txt
    } else {
        exit
    }
}

Write-Host "`n✅ All dependencies installed" -ForegroundColor Green

# Run agent
Write-Host "`n🚀 Starting production voice agent...`n" -ForegroundColor Cyan
python voice_agent_production.py
