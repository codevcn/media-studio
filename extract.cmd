@echo off
setlocal

python "%~dp0/src/features/audio/extract_audio/extract_audio.py" %*
if errorlevel 1 (
    echo.
    echo Co loi xay ra.
    pause
)

endlocal