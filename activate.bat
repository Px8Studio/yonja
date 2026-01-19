@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM 🌿 Yonca AI - Quick Environment Activation (CMD version)
REM ═══════════════════════════════════════════════════════════════════════

if "%1"=="-info" goto :info
if "%1"=="--info" goto :info

echo.
echo 🌿 Activating Yonca AI environment...

if exist ".venv\Scripts\activate.bat" (
    echo ✓ Using existing virtual environment
    call .venv\Scripts\activate.bat
    echo.
    echo ✅ Environment activated! Available commands:
    echo    uvicorn yonca.api.main:app --reload   # Start API
    echo    alembic upgrade head                  # Run migrations
    echo    chainlit run demo-ui/app.py           # Start UI
    echo.
    echo    Run 'activate.bat -info' for more options
    echo.
) else (
    echo ⚠️  No .venv found. Run: poetry install
    exit /b 1
)
goto :eof

:info
echo.
echo 🌿 Yonca AI Development Environment
echo ═══════════════════════════════════════════════════════════════
echo.
echo 📦 Option 1: Use Poetry Shell (Recommended)
echo    poetry shell
echo    uvicorn yonca.api.main:app --reload
echo    alembic upgrade head
echo.
echo ⚡ Option 2: Use Poetry Run (No activation needed)
echo    poetry run dev                # Start FastAPI
echo    poetry run migrate            # Run migrations
echo    poetry run seed               # Seed database
echo.
echo 🎯 Option 3: Use Full Paths
echo    .venv\Scripts\python.exe -m uvicorn yonca.api.main:app --reload
echo    .venv\Scripts\alembic.exe upgrade head
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
