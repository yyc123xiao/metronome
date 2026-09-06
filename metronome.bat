@echo off
rem 节拍器启动器：以无终端窗口方式启动图形界面
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0metronome.py"
) else (
    start "" python "%~dp0metronome.py"
)
exit /b 0
