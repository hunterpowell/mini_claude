@echo off
REM Launch the Claude pet with no console window, on the clean Python 3.12
REM (Anaconda's bundled Qt conflicts with PyQt6, so we avoid it here).
start "" "C:\Users\Hunter\AppData\Local\Programs\Python\Python312\pythonw.exe" "%~dp0pet.py"
