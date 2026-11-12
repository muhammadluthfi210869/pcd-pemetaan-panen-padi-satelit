@echo off
echo ====================================================================
echo   PCD Web App: Pemetaan Kesiapan Panen Padi Satelit Jawa Barat
echo   Politeknik Negeri Bandung (POLBAN) - Semester 5
echo ====================================================================
echo   Membuka server di: http://127.0.0.1:8000
echo   Tekan Ctrl+C untuk menghentikan server.
echo ====================================================================
cd /d "%~dp0"
"..\Pertemuan 1\venv\Scripts\uvicorn.exe" main:app --reload --port 8000
pause
