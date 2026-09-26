@echo off
REM Sweet Diagnosis - start the app (Windows). Double-click this file.

cd /d "%~dp0"

IF EXIST ".venv\Scripts\activate.bat" CALL ".venv\Scripts\activate.bat"

REM Uncomment the next line to let phones on the same Wi-Fi reach this laptop:
REM SET SWEET_HOST=0.0.0.0

python app.py

echo.
echo The server has stopped. Press any key to close this window.
pause >nul
