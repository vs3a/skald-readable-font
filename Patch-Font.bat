@echo off
rem SKALD Readable Font Mod - launcher (runs Patch-Font.ps1; nothing to install)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Patch-Font.ps1" %*
echo.
pause
