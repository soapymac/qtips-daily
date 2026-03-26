@echo off
title Q-Tips: Fetch Odds + Push to Cloud
echo.
echo  ==========================================
echo   Q-Tips: Fetch Betfair Odds ^& Push
echo  ==========================================
echo.
echo  This fetches live odds from Betfair and
echo  pushes them to GitHub for the cloud pipeline.
echo.
echo  [1] Fetching tomorrow's odds...
echo.

cd /d "%~dp0"
cd ..

:: Determine tomorrow's date
for /f %%i in ('python -c "from datetime import datetime, timedelta; print((datetime.now() + timedelta(days=1)).strftime('%%Y-%%m-%%d'))"') do set TOMORROW=%%i
echo  Target date: %TOMORROW%
echo.

:: Run the Betfair odds fetcher
python scripts/fetch_cloud_odds.py --date %TOMORROW%

if errorlevel 1 (
    echo.
    echo  [ERROR] Failed to fetch odds. Check your credentials.
    pause
    exit /b 1
)

echo.
echo  [2] Pushing odds to GitHub...
echo.

git add live_odds/
git commit -m "Pre-push Betfair odds for %TOMORROW%"
git push origin2 master:main

if errorlevel 1 (
    echo.
    echo  [WARN] Push failed - trying force push...
    git push origin2 master:main --force
)

echo.
echo  ==========================================
echo   DONE! Odds are now on GitHub.
echo   The cloud pipeline will use them.
echo  ==========================================
echo.
pause
