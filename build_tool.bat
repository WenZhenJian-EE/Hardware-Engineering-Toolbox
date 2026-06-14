@echo off
echo =========================================================
echo Circuit Calculator Hardware Toolbox - Pyinstaller Builder
echo =========================================================

echo Checking for PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller not found. Installing now...
    pip install pyinstaller matplotlib PyQt5 -q
)

echo.
echo Building executable...
echo This may take a few minutes. Please wait...

:: We use -w (no console window) and -F (onefile execution)
pyinstaller --noconfirm --log-level=WARN ^
    --onedir ^
    --windowed ^
    --name "Circuit_Calculator_Pro" ^
    --icon=NONE ^
    --add-data "cmd_buttons.json;." ^
    --add-data "app_config.json;." ^
    main.py

echo.
if exist "dist\Circuit_Calculator_Pro\Circuit_Calculator_Pro.exe" (
    echo [SUCCESS] Build completed successfully!
    echo Your application is located in the "dist\Circuit_Calculator_Pro" folder.
) else (
    echo [ERROR] Build failed. Please check the logs above.
)

pause
