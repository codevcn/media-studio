@echo off
:: slice.cmd - Wrapper to run slice_audio.py
:: Usage: slice.cmd "D:/data/audio.wav" 50
:: Supported: .wav .mp3 .mp4

setlocal

if "%~1"=="" (
    echo Usage  : slice.cmd ^<input_file^> ^<size_mb^>
    echo Example: slice.cmd "D:/data/audio.wav" 50
    echo Formats: .wav  .mp3  .mp4
    exit /b 1
)

if "%~2"=="" (
    echo [ERROR] Missing size_mb argument.
    echo Usage: slice.cmd ^<input_file^> ^<size_mb^>
    exit /b 1
)

:: Lay duong dan thu muc chua file .cmd nay de tim slice_audio.py
set "SCRIPT_DIR=%~dp0"

python "%SCRIPT_DIR%/src/features/media/slice_media.py" %1 %2

endlocal