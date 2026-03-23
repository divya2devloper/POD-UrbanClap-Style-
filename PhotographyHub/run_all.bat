@echo off
setlocal

:: 1. Check if Docker is available
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Docker not found. Falling back to Local Native Startup...
    echo.
    echo Ensure Redis is running locally on port 6379!
    echo.
    
    echo [INFO] Starting background services...
    
    :: Start Celery Worker in new window with tracking title
    start "PH-Worker" cmd /c "..\.venv\Scripts\python.exe -m celery -A core worker -l info"
    
    :: Start Celery Beat in new window with tracking title
    start "PH-Beat" cmd /c "..\.venv\Scripts\python.exe -m celery -A core beat -l info"
    
    echo.
    echo ==========================================
    echo LOCAL SERVICES STARTING...
    echo ==========================================
    echo Website: http://127.0.0.1:8000
    echo (Press CTRL+C in THIS window to stop all services)
    echo ==========================================
    echo.
    
    :: Run Django Server in THIS window (Foreground)
    ..\.venv\Scripts\python.exe manage.py runserver
    
    :: When server stops, kill the background windows
    echo.
    echo [INFO] Web server stopped. Cleaning up background services...
    taskkill /FI "WINDOWTITLE eq PH-*" /F /T >nul 2>&1
    
    echo [SUCCESS] All services stopped.
    timeout /t 3 >nul
    exit /b
)

echo [INFO] Docker detected. Starting PhotographyHub via Docker Compose...

:: 2. Docker logic
docker compose down --remove-orphans
docker compose up --build -d

echo.
echo ==========================================
echo DOCKER SERVICES STARTED SUCCESSFULLY
echo ==========================================
echo Website: http://localhost:8000
echo Redis:   localhost:6379
echo DB:      localhost:5432
echo ==========================================
echo.
echo View Logs: docker compose logs -f web
pause
