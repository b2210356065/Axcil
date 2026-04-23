@echo off
REM ExcelAI FastAPI Backend Server Starter
REM Flutter Windows Desktop için

echo ========================================
echo ExcelAI API Server Baslatiliyor...
echo ========================================
echo.

cd /d C:\Users\azsxd\OneDrive\Masaüstü\ExcelAI

REM Virtual environment kontrol (varsa aktif et)
if exist venv\Scripts\activate.bat (
    echo Virtual environment aktif ediliyor...
    call venv\Scripts\activate.bat
)

echo Dependencies kontrol ediliyor...
pip install -q fastapi uvicorn python-multipart
echo.

echo Server baslatiliyor: http://127.0.0.1:8000
echo API Docs: http://127.0.0.1:8000/docs
echo.
echo Sunucuyu durdurmak icin CTRL+C basin.
echo ========================================
echo.

python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --reload

pause
