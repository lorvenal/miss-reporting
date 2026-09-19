@echo off
REM x
echo [31mInstalling dependencies...[0m
python -m pip install --upgrade pip
python -m pip install requests colorama

REM x
echo [31mStarting main.py...[0m
python main.py

REM x
echo [31mPress any key to exit...[0m
pause >nul