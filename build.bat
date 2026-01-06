@echo off
echo ========================================
echo    Screen Monitor - Build Script
echo ========================================
echo.

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller --noconfirm --onefile --windowed ^
    --name "ScreenMonitor" ^
    --icon=NONE ^
    --add-data "C:\Users\kolod\AppData\Local\Programs\Python\Python*\Lib\site-packages\customtkinter;customtkinter" ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageGrab ^
    --hidden-import=numpy ^
    --hidden-import=customtkinter ^
    screen_monitor.py

echo.
echo ========================================
echo Build complete! 
echo Executable is in the 'dist' folder.
echo ========================================
pause
