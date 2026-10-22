@echo off
rem Builds SKALD-Font-Patcher.exe (needs: py -3 -m pip install UnityPy Pillow pyinstaller)
rem Run it from a short path (e.g. C:\build) - some tools fail on paths over 260 characters.
cd /d "%~dp0"
py -3 -m PyInstaller --noconfirm --onefile --console --name SKALD-Font-Patcher ^
  --add-data "glyphs_04b.json;." ^
  --collect-all UnityPy --collect-all archspec --collect-all etcpak --collect-all texture2ddecoder --collect-all astc_encoder ^
  --exclude-module pyfmodex --exclude-module fmod_toolkit ^
  --exclude-module tkinter --exclude-module matplotlib --exclude-module numpy --exclude-module scipy --exclude-module IPython ^
  patch_font.py
echo.
echo Result: dist\SKALD-Font-Patcher.exe
