@echo off
title Push CareerPilot AI to GitHub
echo ================================================================
echo               Pushing CareerPilot AI to GitHub
echo ================================================================
echo.

git remote remove origin 2>nul
git remote add origin https://github.com/preethamn023/CareerPilot-AI.git
git branch -M main

echo Step 1: Connecting to GitHub repository...
echo Step 2: Pushing code...
echo (If prompted, click 'Sign in with your browser' in the popup)
echo.

git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ================================================================
    echo [SUCCESS] Code pushed successfully!
    echo.
    echo Shareable Link:
    echo https://github.com/preethamn023/CareerPilot-AI
    echo ================================================================
) else (
    echo ================================================================
    echo [ERROR] Push failed. 
    echo Please make sure you created the repository first:
    echo 1. Go to https://github.com/new
    echo 2. Set repository name to: CareerPilot-AI
    echo 3. Click 'Create repository'
    echo 4. Run this script again!
    echo ================================================================
)
echo.
pause
