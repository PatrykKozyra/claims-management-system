# Quick Sync Reference Card

**Fast reference for syncing between Private and Enterprise GitHub**

---

## One-Time Setup (Business Laptop)

```bash
# 1. Clone from private GitHub
git clone https://github.com/PatrykKozyra/claims-management-system.git
cd claims-management-system

# 2. Add enterprise remote
git remote add enterprise https://github.com/YourEnterpriseOrg/claims-management-system.git

# 3. Configure credentials
git config credential.helper manager

# 4. Test push (will save credentials)
git push enterprise main
```

✅ Done! You're ready to sync.

---

## Daily Workflow

### Private Laptop (Development)

```bash
# Morning: Pull latest
git pull origin main

# Work: Make changes with Claude Code
# ... development ...

# Evening: Push changes
git add .
git commit -m "Description of changes"
git push origin main
```

### Business Laptop (Sync)

**Option 1: Use Script** (⚡ Fastest)
```bash
# Double-click sync-to-enterprise.bat
# Or run: .\sync-to-enterprise.bat
```

**Option 2: Manual** (2 commands)
```bash
git pull origin main
git push enterprise main
```

**Option 3: One-Liner**
```bash
git pull origin main && git push enterprise main
```

---

## Common Commands

```bash
# Check status
git status

# Check remotes
git remote -v

# View recent commits
git log -5 --oneline

# Sync (manual)
git pull origin main && git push enterprise main

# Force sync (use carefully!)
git push enterprise main --force
```

---

## Troubleshooting

### Authentication Failed
```bash
# Re-authenticate
git push enterprise main
# Enter credentials when prompted
```

### Push Rejected
```bash
# Pull first, then push
git pull enterprise main
git push enterprise main
```

### Check Sync Status
```bash
# See differences
git log origin/main..enterprise/main
```

---

## Emergency Procedures

### Undo Last Commit
```bash
git revert HEAD
git push enterprise main
```

### Reset to Previous Commit (⚠️ Dangerous)
```bash
git reset --hard HEAD~1
git push enterprise main --force
```

---

## File Locations

- **Batch Script**: `sync-to-enterprise.bat`
- **PowerShell Script**: `Sync-ToEnterprise.ps1`
- **Full Guide**: `DUAL_REPO_WORKFLOW.md`

---

## Support

Need help? See `DUAL_REPO_WORKFLOW.md` for:
- Detailed explanations
- Advanced scenarios
- Conflict resolution
- Security considerations

---

*Quick reference for daily use - Keep handy!*
