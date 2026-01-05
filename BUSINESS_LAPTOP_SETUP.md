# Business Laptop Setup Guide

**Quick Start Guide for Stakeholder Presentation**

This guide helps you clone and run the Claims Management System on your business laptop with all test data ready for demonstration.

---

## ✅ Good News - Test Data Included!

Your repository **includes a pre-populated database** with:
- **6 Users** (admin + team members with different roles)
- **262 Claims** (various statuses and types)
- **184 Voyages** (assigned and unassigned)
- **25 Ship Owners**
- **80 Ships** (including TC fleet data)
- **993 Port Activities**

**Database Size**: 2.5 MB (included in GitHub repo)

---

## Prerequisites

### Required Software

1. **Python 3.11 or 3.12**
   - Download: https://www.python.org/downloads/
   - ⚠️ **Important**: Check "Add Python to PATH" during installation

2. **Git** (if not already installed)
   - Download: https://git-scm.com/downloads

3. **Code Editor** (optional, for viewing)
   - VS Code: https://code.visualstudio.com/

---

## Setup Steps

### Step 1: Clone the Repository

Open Command Prompt or PowerShell and run:

```bash
cd C:\Users\YourUsername\Documents  # Or your preferred location
git clone https://github.com/PatrykKozyra/claims-management-system.git
cd claims-management-system
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows CMD:
venv\Scripts\activate

# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# You should see (venv) prefix in your terminal
```

**PowerShell Note**: If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages (Django, DRF, etc.)

### Step 4: Apply Migrations (Optional - Database Already Populated)

The database is already included with test data, but if needed:

```bash
python manage.py migrate
```

### Step 5: Run the Server

```bash
python manage.py runserver 8000
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Step 6: Access the Application

Open your browser and navigate to:
- **Main App**: http://localhost:8000/
- **Login Page**: http://localhost:8000/login/

---

## Test User Accounts

Use these accounts to demonstrate different user roles:

### Admin Account (Full Access)
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: ADMIN (all permissions)

### Analyst Accounts

1. **John Smith** - Write Access
   - Username: `john.smith`
   - Password: `password123`
   - Role: WRITE (can create/edit claims)

2. **Jane Doe** - Write Access
   - Username: `jane.doe`
   - Password: `password123`
   - Role: WRITE (can create/edit claims)

3. **Bob Wilson** - Read + Export
   - Username: `bob.wilson`
   - Password: `password123`
   - Role: READ_EXPORT (can view and export)

4. **Alice Brown** - Read Only
   - Username: `alice.brown`
   - Password: `password123`
   - Role: READ (view only)

---

## Features to Demonstrate

### 1. **User Roles & Permissions**
- Login as different users to show role-based access
- Admin can create users and manage everything
- READ users can only view
- WRITE users can edit and update

### 2. **Claims Management**
- View claims list with filters
- ⚠️ **Note**: "New Claim" button removed (RADAR-only creation)
- Show claim details, status updates
- Add comments and documents
- Update payment status

### 3. **Voyage Assignment**
- Show voyage list
- Demonstrate voyage assignment to analysts
- Track assignment history

### 4. **Ship Fleet Management**
- Browse ships master data
- Show TC fleet tracking
- Display charter status indicators

### 5. **Port Activities**
- View port activities timeline
- Show activity types (Loading, Discharging, STS, etc.)
- Demonstrate pivot table view

### 6. **Analytics Dashboard**
- Show claims statistics
- Payment status breakdown
- Ship owner analytics
- Export to Excel

### 7. **User Directory**
- Browse all users
- Show user profiles with photos
- Filter by role and department

---

## Database Reset (If Needed)

If you need to reset the database or add more data:

### Option 1: Re-populate from Scratch

```bash
# Delete existing data
python manage.py flush --no-input

# Run all population commands
python manage.py populate_dummy_data
python manage.py populate_tc_fleet_data
python manage.py populate_activity_types
python manage.py populate_port_activities
python manage.py populate_ship_specifications
```

### Option 2: Add More Data

```bash
# Add more claims and voyages
python manage.py populate_tc_fleet_voyages

# Simulate RADAR import
python manage.py simulate_radar_import
```

---

## Troubleshooting

### Port Already in Use

If port 8000 is busy:
```bash
python manage.py runserver 8005
# Then access at http://localhost:8005/
```

### Virtual Environment Not Activating

**On Windows**:
```bash
# Try full path:
C:\path\to\claims-management-system\venv\Scripts\activate
```

### Missing Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Database Error

If database is corrupted:
```bash
# The database should work as-is, but if needed:
python manage.py migrate --run-syncdb
```

### Static Files Not Loading

```bash
python manage.py collectstatic --no-input
```

---

## Quick Presentation Checklist

Before your stakeholder meeting:

- [ ] Clone repository to business laptop
- [ ] Create and activate virtual environment
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Run server (`python manage.py runserver`)
- [ ] Test admin login (admin/admin123)
- [ ] Test regular user login (john.smith/password123)
- [ ] Verify claims list loads with data
- [ ] Check voyages page works
- [ ] Test ship fleet page
- [ ] Verify port activities page
- [ ] Test analytics dashboard
- [ ] Prepare any specific features to highlight

---

## Features Highlights for Stakeholders

### Key Selling Points

1. **RADAR Integration Ready**
   - Claims synced from RADAR (creation disabled in UI)
   - Single source of truth
   - Placeholder code ready for API integration

2. **Comprehensive User Management**
   - 5 role levels (READ, READ_EXPORT, WRITE, TEAM_LEAD, ADMIN)
   - Password change on first login
   - User directory with profiles

3. **Claims Lifecycle**
   - Full claim tracking from draft to settlement
   - Payment status integration with RADAR
   - Time-bar detection
   - Activity logging

4. **Ship Fleet Integration**
   - Ship master data management
   - TC fleet tracking with expiry warnings
   - Charter status indicators

5. **Port Activities Timeline**
   - Real-time activity tracking
   - RADAR sync capability
   - Pivot table views

6. **Security Features**
   - Role-based access control
   - Optimistic locking (prevents conflicts)
   - Comprehensive error handling
   - Audit trail for all changes

7. **Testing & Quality**
   - 173 automated tests passing
   - 70%+ code coverage
   - CI/CD ready (GitHub Actions configured)

---

## Network Considerations

### Corporate Firewall

If your business laptop has firewall restrictions:

1. **Local Development**: The app runs entirely locally (no external connections needed for demo)
2. **Port Access**: Only needs localhost:8000 (internal only)
3. **No Internet Required**: Once dependencies are installed, works offline

### If Behind Proxy

Add to your environment before `pip install`:
```bash
set HTTP_PROXY=http://your-proxy:port
set HTTPS_PROXY=http://your-proxy:port
pip install -r requirements.txt
```

---

## Post-Presentation

### Collecting Feedback

Create a file to track stakeholder feedback:
```bash
# In the project directory
notepad STAKEHOLDER_FEEDBACK.md
```

### Export Demo Data

If stakeholders want to see the data:
```bash
# Export all claims to Excel
# Login as admin, go to Analytics > Export
```

---

## Additional Resources

### Documentation
- **Setup Guide**: [docs/setup/SETUP_GUIDE.md](docs/setup/SETUP_GUIDE.md)
- **User Guide**: [docs/features/](docs/features/)
- **API Documentation**: [docs/api/API_GUIDE.md](docs/api/API_GUIDE.md)
- **Testing Guide**: [docs/development/TESTING.md](docs/development/TESTING.md)

### Support
- **GitHub Issues**: https://github.com/PatrykKozyra/claims-management-system/issues
- **Project Status**: [docs/project/STATUS.md](docs/project/STATUS.md)
- **Changelog**: [docs/project/CHANGELOG.md](docs/project/CHANGELOG.md)

---

## Summary

### What's Included
✅ Pre-populated database with 1,500+ records
✅ 6 test users with different roles
✅ All dependencies in requirements.txt
✅ Comprehensive documentation
✅ Ready-to-run development server

### What You Need
- Python 3.11+
- 5 minutes setup time
- Internet for cloning repo and installing packages
- Browser to view application

### Expected Demo Flow
1. Clone repo (1 min)
2. Setup virtual env (1 min)
3. Install dependencies (2-3 min)
4. Run server (immediate)
5. **Ready to present!**

---

**Good luck with your presentation!** 🎉

If you encounter any issues during setup on your business laptop, check the troubleshooting section or refer to the detailed [SETUP_GUIDE.md](docs/setup/SETUP_GUIDE.md).

---

*Last Updated: January 5, 2026*
