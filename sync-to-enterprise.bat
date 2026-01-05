@echo off
REM ============================================
REM Sync from Private to Enterprise GitHub
REM ============================================

echo.
echo ============================================
echo Syncing from Private to Enterprise GitHub
echo ============================================
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo Error: Not in a git repository!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Step 1: Fetch from private GitHub
echo [1/4] Fetching from private GitHub...
git fetch origin
if errorlevel 1 (
    echo Error: Failed to fetch from private GitHub
    pause
    exit /b 1
)
echo     Done!
echo.

REM Step 2: Pull latest changes
echo [2/4] Pulling latest changes from private GitHub...
git pull origin main
if errorlevel 1 (
    echo Error: Failed to pull from private GitHub
    echo Please resolve any merge conflicts and try again.
    pause
    exit /b 1
)
echo     Done!
echo.

REM Step 3: Push to enterprise GitHub
echo [3/4] Pushing to enterprise GitHub...
git push enterprise main
if errorlevel 1 (
    echo Error: Failed to push to enterprise GitHub
    echo Please check your credentials and network connection.
    pause
    exit /b 1
)
echo     Done!
echo.

REM Step 4: Verify
echo [4/4] Verifying sync...
git log -1 --oneline
echo.

echo ============================================
echo Sync Complete!
echo ============================================
echo.
echo Both repositories are now in sync.
echo Latest commit has been pushed to enterprise GitHub.
echo.

pause
