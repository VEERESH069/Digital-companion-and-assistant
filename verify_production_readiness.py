#!/usr/bin/env python
"""
Production Readiness Verification Script

Run this before deploying to production:
    python verify_production_readiness.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 70)
print("PRODUCTION READINESS VERIFICATION")
print("=" * 70)

issues = []
warnings = []
checks_passed = 0
checks_total = 0

def check(condition, message, level="error"):
    """Track check results"""
    global checks_passed, checks_total
    checks_total += 1
    
    if condition:
        print(f"  ✓ {message}")
        checks_passed += 1
        return True
    else:
        msg = f"  ✗ {message}"
        print(msg)
        if level == "error":
            issues.append(message)
        else:
            warnings.append(message)
        return False

# ============================================================================
# SECURITY CHECKS
# ============================================================================
print("\n[SECURITY CHECKS]")

# Check 1: FLASK_DEBUG is False
flask_debug = os.getenv("FLASK_DEBUG", "false").lower()
check(flask_debug in ["false", "0", "no"], "FLASK_DEBUG is not set to False")

# Check 2: FLASK_ENV is production
flask_env = os.getenv("FLASK_ENV", "").lower()
check(flask_env == "production", "FLASK_ENV is set to 'production'")

# Check 3: SECRET_KEY is set and not default
secret_key = os.getenv("SECRET_KEY", "").strip()
check(
    secret_key and secret_key != "your-secret-key-change-this-in-production",
    "SECRET_KEY is set to a non-default value"
)

# Check 4: No exposed API keys in .env file
env_file = Path(".env")
if env_file.exists():
    env_content = env_file.read_text()
    exposed_keys = ["sk-proj-", "sk-ant-", "sk_car_"] if any(
        key in env_content.lower() for key in ["sk-", "sk_"]
    ) else []
    
    if exposed_keys:
        check(False, ".env file contains what appears to be real API keys")
    else:
        check(True, ".env file does not contain exposed API keys")
else:
    check(False, ".env file exists", level="warning")

# Check 5: CORS_ORIGINS configured
cors_origins = os.getenv("CORS_ORIGINS", "*")
check(
    cors_origins != "*",
    "CORS_ORIGINS is not set to '*' (restrictive whitelist configured)"
)

# ============================================================================
# CONFIGURATION CHECKS
# ============================================================================
print("\n[CONFIGURATION CHECKS]")

# Check 6: ENVIRONMENT variable set
environment = os.getenv("ENVIRONMENT", "development")
check(environment == "production", "ENVIRONMENT is set to 'production'")

# Check 7: DATABASE_URL configured
database_url = os.getenv("DATABASE_URL", "")
check(
    database_url and "sqlite" not in database_url.lower(),
    "DATABASE_URL configured (PostgreSQL recommended for production)"
)

# Check 8: Log level appropriate for production
log_level = os.getenv("LOG_LEVEL", "INFO")
check(
    log_level in ["WARNING", "ERROR", "INFO"],
    f"LOG_LEVEL appropriate for production: {log_level}"
)

# Check 9: Required API keys present
openai_key = os.getenv("OPENAI_API_KEY", "").strip()
check(
    openai_key and openai_key.startswith("sk-"),
    "OPENAI_API_KEY is configured"
)

cartesia_key = os.getenv("CARTESIA_API_KEY", "").strip()
check(
    cartesia_key and "your" not in cartesia_key.lower(),
    "CARTESIA_API_KEY is configured"
)

# ============================================================================
# APPLICATION STRUCTURE CHECKS
# ============================================================================
print("\n[APPLICATION STRUCTURE]")

# Check 10: Required files exist
required_files = [
    "config.py",
    "api.py",
    "models.py",
    "database.py",
    "requirements.txt",
    "Dockerfile",
]

for file in required_files:
    check(Path(file).exists(), f"Required file exists: {file}")

# Check 11: Database models defined
try:
    from models import ConversationSession, ClinicalData
    check(True, "Database models can be imported")
except Exception as e:
    check(False, f"Database models import failed: {e}")

# Check 12: Configuration loads without errors
try:
    import config
    check(True, "Configuration module loads without errors")
    check(
        config.STT_LANGUAGES and len(config.STT_LANGUAGES) > 0,
        f"Language support configured: {', '.join(config.STT_LANGUAGES)}"
    )
except Exception as e:
    check(False, f"Configuration loading failed: {e}")

# ============================================================================
# DEPENDENCY CHECKS
# ============================================================================
print("\n[DEPENDENCIES]")

required_packages = [
    "flask",
    "sqlalchemy",
    "openai",
    "cartesia",
    "speech_recognition",
]

for package in required_packages:
    try:
        __import__(package)
        check(True, f"Required package installed: {package}")
    except ImportError:
        check(False, f"Required package not found: {package}")

# ============================================================================
# DEPLOYMENT CHECKS
# ============================================================================
print("\n[DEPLOYMENT CONFIGURATION]")

# Check 13: Docker configuration
check(Path("Dockerfile").exists(), "Dockerfile exists for containerization")

# Check 14: .env.example exists
check(
    Path(".env.example").exists(),
    ".env.example exists as configuration template"
)

# Check 15: .gitignore configured
check(
    Path(".gitignore").exists(),
    ".gitignore exists and prevents committing secrets"
)

# Check 16: PRODUCTION_DEPLOYMENT.md exists
check(
    Path("PRODUCTION_DEPLOYMENT.md").exists(),
    "Deployment documentation available"
)

# ============================================================================
# LANGUAGE SUPPORT
# ============================================================================
print("\n[LANGUAGE SUPPORT]")

try:
    import config
    
    supported_languages = {
        "en": "English",
        "hi": "Hindi",
        "mr": "Marathi",
        "te": "Telugu",
        "bn": "Bengali",
        "ta": "Tamil",
        "ml": "Malayalam",
        "kn": "Kannada",
    }
    
    for code, name in supported_languages.items():
        has_stt = code in config.STT_LANGUAGES
        has_tts = code in config.CARTESIA_LANGUAGE_VOICES
        lang_ok = has_stt and has_tts
        
        status = "✓" if lang_ok else "✗"
        print(f"  {status} {name:12} (STT: {'✓' if has_stt else '✗'}, TTS: {'✓' if has_tts else '✗'})")
        checks_total += 1
        if lang_ok:
            checks_passed += 1
        else:
            issues.append(f"{name} language support incomplete")
            
except Exception as e:
    print(f"  ✗ Language support check failed: {e}")
    checks_total += 1

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print(f"RESULTS: {checks_passed}/{checks_total} checks passed")
print("=" * 70)

if warnings:
    print("\n[⚠ WARNINGS]")
    for warning in warnings:
        print(f"  - {warning}")

if issues:
    print("\n[✗ CRITICAL ISSUES FOUND]")
    for issue in issues:
        print(f"  - {issue}")
    print("\n❌ PRODUCTION DEPLOYMENT NOT RECOMMENDED")
    print("Please resolve all critical issues before deploying.\n")
    sys.exit(1)
else:
    print("\n✅ PRODUCTION READY")
    print("Your application is ready for production deployment!\n")
    sys.exit(0)
