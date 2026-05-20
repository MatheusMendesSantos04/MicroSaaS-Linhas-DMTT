@echo off
echo Iniciando MicroSaaS Linhas DMTT...

start "Backend - FastAPI" cmd /k "cd /d I:\Micro-SaaS-DMTT\MicroSaaS-Linhas-DMTT\backend && python -m uvicorn app.main:app --reload"

timeout /t 3 /nobreak >nul

start "Frontend - Vite" cmd /k "cd /d I:\Micro-SaaS-DMTT\MicroSaaS-Linhas-DMTT\frontend && npm run dev"

timeout /t 4 /nobreak >nul

start "" "http://localhost:5173"

echo.
echo Servidores iniciados!
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
echo Feche as janelas de Backend e Frontend para encerrar.
