@echo off
REM Windows için başlatma script'i

echo ========================================
echo SUBU Mevzuat Chatbot Baslatiliyor...
echo ========================================
echo.

cd backend

REM Virtual environment'i aktif et
call venv\Scripts\activate.bat

REM Sunucuyu başlat
echo Sunucu baslatiliyor...
python run_server.py

pause
