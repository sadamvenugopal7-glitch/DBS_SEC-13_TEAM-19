@echo off
title Wines Management System - Flask Server
cd /d "%~dp0"
echo ========================================================
echo   Starting WINES MANAGEMENT SYSTEM (Team 19, Section 3)
echo ========================================================
echo Server starting at http://127.0.0.1:5000 ...
start http://127.0.0.1:5000
python backend\app.py
pause
