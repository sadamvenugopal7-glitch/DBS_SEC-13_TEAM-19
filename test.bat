@echo off
title Wines Management System - Automated Test Suite
cd /d "%~dp0wines-management-system"
echo ========================================================
echo   Running Automated Test Suite (35 Tests)
echo ========================================================
python backend\test_system.py
pause
