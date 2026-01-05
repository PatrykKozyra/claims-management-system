# Dual Repository Workflow Guide

**Managing Development Between Private and Enterprise GitHub Accounts**

This guide helps you efficiently manage development on your private laptop (with Claude Code) and deployment on your business laptop (with enterprise GitHub).

---

## Overview

### The Challenge

- **Private Laptop**: Development machine with Claude Code access
- **Private GitHub**: https://github.com/PatrykKozyra/claims-management-system
- **Business Laptop**: No Claude Code, no private GitHub access
- **Enterprise GitHub**: Work repository for deployment
- **Requirement**: Keep both repositories in sync efficiently

### The Solution

Use a **bridge workflow** where your business laptop acts as a bridge between private and enterprise GitHub accounts.

---

## Workflow Diagram

```
Private Laptop (Development)
    ↓ (git push)
Private GitHub Repo
    ↓ (git clone/pull on business laptop)
Business Laptop (Bridge)
    ↓ (git push)
Enterprise GitHub Repo
```

---

## Initial Setup

### Step 1: Setup on Business Laptop

#### 1.1 Configure Git with Enterprise Email

```bash
# Set your enterprise email globally
git config --global user.name "Your Name"
git config --global user.email "your.email@enterprise.com"
```

#### 1.2 Clone Private Repository

```bash
# Navigate to your workspace
cd C:\Users\YourName\Documents\Projects

# Clone from private GitHub (one-time setup)
git clone https://github.com/PatrykKozyra/claims-management-system.git
cd claims-management-system
```

#### 1.3 Add Enterprise Remote

```bash
# Add enterprise GitHub as second remote
git remote add enterprise https://github.com/YourEnterpriseOrg/claims-management-system.git

# Verify remotes
git remote -v
```

You should see:
```
origin    https://github.com/PatrykKozyra/claims-management-system.git (fetch)
origin    https://github.com/PatrykKozyra/claims-management-system.git (push)
enterprise https://github.com/YourEnterpriseOrg/claims-management-system.git (fetch)
enterprise https://github.com/YourEnterpriseOrg/claims-management-system.git (push)
```

#### 1.4 Authenticate with Enterprise GitHub

```bash
# Push to enterprise (will prompt for credentials)
git push enterprise main

# If using Personal Access Token (PAT):
# 1. Go to enterprise GitHub → Settings → Developer settings → Personal access tokens
# 2. Generate new token with 'repo' scope
# 3. Use token as password when prompted
```

**Save Credentials (Optional)**:
```bash
# Cache credentials for 1 hour (3600 seconds)
git config credential.helper 'cache --timeout=3600'

# Or use Windows Credential Manager (permanent)
git config credential.helper manager
```

---

## Daily Workflow

### On Private Laptop (Development)

#### Morning: Start Development

```bash
# 1. Pull latest changes (if any from enterprise)
git pull origin main

# 2. Create feature branch (optional but recommended)
git checkout -b feature/your-feature-name

# 3. Develop with Claude Code
# Make your changes...

# 4. Test locally
python manage.py runserver
```

#### Evening: Push Changes

```bash
# 1. Check what changed
git status
git diff

# 2. Stage changes
git add .

# 3. Commit with descriptive message
git commit -m "Add feature: description of changes

- Detailed change 1
- Detailed change 2
- etc.

🤖 Generated with Claude Code"

# 4. Push to private GitHub
git push origin main
# Or if on feature branch:
git push origin feature/your-feature-name
```

---

### On Business Laptop (Bridge & Deploy)

#### Method 1: Quick Sync (Recommended)

**Create a sync script** for efficiency.

**File**: `sync-to-enterprise.bat` (Windows)

```batch
@echo off
echo ============================================
echo Syncing from Private to Enterprise GitHub
echo ============================================

echo.
echo [1/4] Fetching from private GitHub...
git fetch origin

echo.
echo [2/4] Pulling latest changes from private GitHub...
git pull origin main

echo.
echo [3/4] Pushing to enterprise GitHub...
git push enterprise main

echo.
echo [4/4] Verifying sync...
git log -1 --oneline

echo.
echo ============================================
echo Sync Complete!
echo ============================================
pause
```

**Usage**:
```bash
# Double-click sync-to-enterprise.bat
# Or run from command line:
sync-to-enterprise.bat
```

---

#### Method 2: Manual Sync (Step by Step)

```bash
# Navigate to project directory
cd C:\Users\YourName\Documents\Projects\claims-management-system

# 1. Check current status
git status

# 2. Fetch updates from private GitHub
git fetch origin

# 3. Pull changes from private GitHub
git pull origin main

# 4. Review changes (optional)
git log -5 --oneline
git diff HEAD~1 HEAD

# 5. Push to enterprise GitHub
git push enterprise main

# 6. Verify push succeeded
git log -1
```

---

#### Method 3: PowerShell Script (Advanced)

**File**: `Sync-ToEnterprise.ps1`

```powershell
# Sync from Private to Enterprise GitHub
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Syncing from Private to Enterprise GitHub" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

try {
    # Check if we're in the right directory
    if (-not (Test-Path ".git")) {
        Write-Host "Error: Not in a git repository!" -ForegroundColor Red
        exit 1
    }

    # Fetch from private GitHub
    Write-Host "[1/5] Fetching from private GitHub..." -ForegroundColor Yellow
    git fetch origin
    if ($LASTEXITCODE -ne 0) { throw "Failed to fetch from origin" }

    # Check for conflicts
    Write-Host "[2/5] Checking for conflicts..." -ForegroundColor Yellow
    $status = git status --porcelain
    if ($status) {
        Write-Host "Warning: Uncommitted changes detected!" -ForegroundColor Yellow
        Write-Host $status
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") { exit 0 }
    }

    # Pull from private GitHub
    Write-Host "[3/5] Pulling latest changes..." -ForegroundColor Yellow
    git pull origin main
    if ($LASTEXITCODE -ne 0) { throw "Failed to pull from origin" }

    # Push to enterprise GitHub
    Write-Host "[4/5] Pushing to enterprise GitHub..." -ForegroundColor Yellow
    git push enterprise main
    if ($LASTEXITCODE -ne 0) { throw "Failed to push to enterprise" }

    # Verify
    Write-Host "[5/5] Verifying sync..." -ForegroundColor Yellow
    $lastCommit = git log -1 --oneline
    Write-Host "Latest commit: $lastCommit" -ForegroundColor Green

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "Sync Complete!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

**Usage**:
```powershell
# Run from PowerShell
.\Sync-ToEnterprise.ps1
```

---

## Advanced Scenarios

### Scenario 1: Merge Feature Branch

**On Private Laptop**:
```bash
# After feature is complete
git checkout main
git merge feature/your-feature-name
git push origin main

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

**On Business Laptop**:
```bash
# Sync as usual
git pull origin main
git push enterprise main
```

---

### Scenario 2: Hotfix on Business Laptop

If you need to make urgent changes on business laptop:

```bash
# 1. Make changes on business laptop
# Edit files...

# 2. Commit changes
git add .
git commit -m "Hotfix: description"

# 3. Push to BOTH repositories
git push origin main        # Push to private GitHub
git push enterprise main    # Push to enterprise GitHub
```

**Then on Private Laptop**:
```bash
# Pull the hotfix
git pull origin main
```

---

### Scenario 3: Resolve Conflicts

If you accidentally work on both laptops:

**On Business Laptop**:
```bash
# Pull from private GitHub
git pull origin main

# If conflicts occur:
# 1. Git will mark conflicting files
# 2. Open files and resolve conflicts manually
# 3. Look for conflict markers:
#    <<<<<<< HEAD
#    Your changes
#    =======
#    Their changes
#    >>>>>>> origin/main

# 4. After resolving:
git add .
git commit -m "Resolve merge conflicts"
git push enterprise main
```

---

### Scenario 4: Sync Specific Branch

```bash
# Pull specific branch from private
git fetch origin
git checkout feature-branch-name
git pull origin feature-branch-name

# Push to enterprise
git push enterprise feature-branch-name
```

---

## Best Practices

### 1. Always Develop on Private Laptop

✅ **DO**: Use private laptop for all development work
❌ **DON'T**: Make code changes on business laptop (except hotfixes)

### 2. Use Business Laptop as Bridge Only

✅ **DO**: Use business laptop to sync changes
✅ **DO**: Use business laptop for presentations
❌ **DON'T**: Use business laptop for primary development

### 3. Sync Daily

```bash
# Best practice: Sync at end of each work day
# On private laptop: git push
# On business laptop: run sync script
```

### 4. Keep Commits Atomic

```bash
# Good commit messages:
git commit -m "Add RADAR-only claims implementation"
git commit -m "Fix voyage assignment bug"

# Bad commit messages:
git commit -m "Updates"
git commit -m "WIP"
```

### 5. Regular Verification

```bash
# Verify both remotes are in sync
git fetch --all
git log --all --graph --oneline -10
```

---

## Quick Reference Commands

### Check Repository Status
```bash
# Check current branch and status
git status

# Check remotes
git remote -v

# Check recent commits
git log -5 --oneline

# Compare branches
git log origin/main..enterprise/main  # Shows commits in enterprise but not in origin
```

### Sync Commands
```bash
# Full sync (pull from private, push to enterprise)
git pull origin main && git push enterprise main

# Force push (use with caution!)
git push enterprise main --force

# Dry run (see what would be pushed)
git push enterprise main --dry-run
```

### Branch Management
```bash
# List all branches
git branch -a

# Create and switch to new branch
git checkout -b feature/new-feature

# Switch to existing branch
git checkout main

# Delete local branch
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature
```

---

## Automation Scripts

### Windows Task Scheduler (Optional)

Automatically sync at specific times:

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Sync GitHub Repos"
4. Trigger: Daily at 9:00 AM (when you arrive at office)
5. Action: Start a program
   - Program: `C:\Users\YourName\Documents\Projects\claims-management-system\sync-to-enterprise.bat`
6. Finish

---

## Troubleshooting

### Issue 1: Authentication Failed

**Problem**: `Authentication failed for enterprise repository`

**Solution**:
```bash
# Use Personal Access Token
# 1. Generate token on enterprise GitHub
# 2. Use token as password
# 3. Save in credential manager:
git config credential.helper manager
```

### Issue 2: Push Rejected

**Problem**: `Updates were rejected because the remote contains work`

**Solution**:
```bash
# Fetch and merge
git fetch enterprise
git merge enterprise/main
git push enterprise main
```

### Issue 3: Different Commit History

**Problem**: Diverged commit history

**Solution**:
```bash
# Option 1: Rebase (cleaner history)
git pull enterprise main --rebase
git push enterprise main

# Option 2: Merge (preserves history)
git pull enterprise main
git push enterprise main
```

### Issue 4: Large Files

**Problem**: Push fails due to large files

**Solution**:
```bash
# Check file sizes
git ls-files -z | xargs -0 du -h | sort -hr | head -20

# Remove large files from git history (if needed)
# Use BFG Repo-Cleaner or git-filter-branch
```

---

## Security Considerations

### 1. Credentials

✅ **DO**: Use Personal Access Tokens (PAT) instead of passwords
✅ **DO**: Store credentials in Windows Credential Manager
❌ **DON'T**: Commit credentials to repository
❌ **DON'T**: Share credentials between accounts

### 2. Environment Variables

Keep `.env` files separate:

```bash
# Private laptop .env
DEBUG=True
SECRET_KEY=dev-secret-key

# Business laptop .env (for demos)
DEBUG=False
SECRET_KEY=demo-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Database

**Private laptop**: Development database (included in repo)
**Business laptop**: Same database for demos

⚠️ **Important**: Don't commit production credentials!

---

## Verification Checklist

Before pushing to enterprise:

- [ ] All tests passing locally
- [ ] No merge conflicts
- [ ] Commit messages are clear
- [ ] No sensitive data in commits
- [ ] `.env` file not committed
- [ ] Requirements.txt updated (if new packages)
- [ ] Documentation updated (if needed)

---

## Emergency Procedures

### If Private GitHub Goes Down

```bash
# On business laptop, continue working
git add .
git commit -m "Emergency commit"
git push enterprise main

# When private GitHub is back:
git push origin main  # Push to private GitHub
```

### If Enterprise GitHub Goes Down

```bash
# Continue development on private laptop
git push origin main

# When enterprise is back, sync from business laptop
```

### If You Need to Undo Last Push

```bash
# On business laptop
git revert HEAD
git push enterprise main

# Or reset (use with extreme caution!)
git reset --hard HEAD~1
git push enterprise main --force
```

---

## Folder Structure Best Practice

Keep consistent structure on both laptops:

```
Private Laptop:
C:\CODE\
└── claims-management-system\

Business Laptop:
C:\Users\YourName\Documents\Projects\
└── claims-management-system\
```

Or use same path if possible:
```
Both Laptops:
C:\Dev\
└── claims-management-system\
```

---

## Example Daily Workflow

### Morning (8:00 AM)

**Private Laptop**:
```bash
# Start work
cd C:\CODE\claims-management-system
git pull origin main
code .  # Open VS Code with Claude
```

### During Day (9:00 AM - 5:00 PM)

**Private Laptop**:
```bash
# Make changes with Claude Code
# Test locally
python manage.py runserver

# Commit periodically
git add .
git commit -m "Add feature X"
```

### End of Day (5:30 PM)

**Private Laptop**:
```bash
# Final push
git add .
git commit -m "Day's work: implemented features X, Y, Z"
git push origin main
```

**Business Laptop** (before leaving office):
```bash
# Sync to enterprise
cd C:\Users\YourName\Documents\Projects\claims-management-system
sync-to-enterprise.bat

# Or manual:
git pull origin main
git push enterprise main
```

---

## Summary

### Key Points

1. **Private Laptop = Development** (with Claude Code)
2. **Business Laptop = Bridge** (sync only)
3. **Private GitHub = Origin** (primary development repo)
4. **Enterprise GitHub = Enterprise** (deployment repo)
5. **Use Scripts** for efficiency (sync-to-enterprise.bat)

### Typical Flow

```
1. Develop on private laptop
2. Push to private GitHub (origin)
3. Pull on business laptop from private GitHub
4. Push from business laptop to enterprise GitHub
5. Repeat
```

### Time Estimate

- Initial setup: 15-20 minutes
- Daily sync: 2-3 minutes
- With automation script: 30 seconds

---

## Additional Resources

### Git Aliases (Optional)

Add to `.gitconfig`:
```
[alias]
    sync-enterprise = !git pull origin main && git push enterprise main
    st = status
    co = checkout
    br = branch
    cm = commit -m
```

Usage:
```bash
git sync-enterprise  # One command to sync!
```

### GUI Tools (Optional)

- **GitHub Desktop**: Visual Git client
- **GitKraken**: Advanced Git GUI
- **SourceTree**: Free Git GUI

All support multiple remotes.

---

**Questions?**

Check the troubleshooting section or refer to:
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com)
- [Git Workflows](https://www.atlassian.com/git/tutorials/comparing-workflows)

---

*Last Updated: January 5, 2026*
