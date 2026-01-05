# ============================================
# Sync from Private to Enterprise GitHub
# PowerShell Script
# ============================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Syncing from Private to Enterprise GitHub" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

try {
    # Check if we're in the right directory
    if (-not (Test-Path ".git")) {
        Write-Host "Error: Not in a git repository!" -ForegroundColor Red
        Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }

    # Check for remotes
    $remotes = git remote
    if ($remotes -notcontains "origin") {
        Write-Host "Error: 'origin' remote not found!" -ForegroundColor Red
        Write-Host "Please configure your remotes first." -ForegroundColor Yellow
        exit 1
    }
    if ($remotes -notcontains "enterprise") {
        Write-Host "Error: 'enterprise' remote not found!" -ForegroundColor Red
        Write-Host "Please add enterprise remote first:" -ForegroundColor Yellow
        Write-Host "  git remote add enterprise <your-enterprise-repo-url>" -ForegroundColor White
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }

    # Step 1: Fetch from private GitHub
    Write-Host "[1/5] Fetching from private GitHub..." -ForegroundColor Yellow
    git fetch origin 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to fetch from private GitHub. Check your network connection."
    }
    Write-Host "      Done!" -ForegroundColor Green
    Write-Host ""

    # Step 2: Check for local changes
    Write-Host "[2/5] Checking for uncommitted changes..." -ForegroundColor Yellow
    $status = git status --porcelain
    if ($status) {
        Write-Host "      Warning: Uncommitted changes detected!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Changed files:" -ForegroundColor White
        Write-Host $status
        Write-Host ""
        $continue = Read-Host "Continue sync anyway? This will not affect uncommitted changes. (y/n)"
        if ($continue -ne "y") {
            Write-Host "Sync cancelled." -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "      No uncommitted changes." -ForegroundColor Green
    }
    Write-Host ""

    # Step 3: Pull from private GitHub
    Write-Host "[3/5] Pulling latest changes from private GitHub..." -ForegroundColor Yellow
    $pullOutput = git pull origin main 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      Error output:" -ForegroundColor Red
        Write-Host $pullOutput
        throw "Failed to pull from private GitHub. Please resolve any merge conflicts and try again."
    }
    Write-Host "      Done!" -ForegroundColor Green
    Write-Host ""

    # Step 4: Push to enterprise GitHub
    Write-Host "[4/5] Pushing to enterprise GitHub..." -ForegroundColor Yellow
    $pushOutput = git push enterprise main 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      Error output:" -ForegroundColor Red
        Write-Host $pushOutput
        throw "Failed to push to enterprise GitHub. Please check your credentials and permissions."
    }
    Write-Host "      Done!" -ForegroundColor Green
    Write-Host ""

    # Step 5: Verify
    Write-Host "[5/5] Verifying sync..." -ForegroundColor Yellow
    $lastCommit = git log -1 --pretty=format:"%h - %s (%an, %ar)"
    Write-Host "      Latest commit:" -ForegroundColor White
    Write-Host "      $lastCommit" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "============================================" -ForegroundColor Green
    Write-Host "Sync Complete!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Both repositories are now in sync." -ForegroundColor White
    Write-Host "Latest commit has been pushed to enterprise GitHub." -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "1. Check your network connection" -ForegroundColor White
    Write-Host "2. Verify your GitHub credentials" -ForegroundColor White
    Write-Host "3. Ensure both remotes are configured correctly:" -ForegroundColor White
    Write-Host "   git remote -v" -ForegroundColor Cyan
    Write-Host "4. Check for merge conflicts:" -ForegroundColor White
    Write-Host "   git status" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
