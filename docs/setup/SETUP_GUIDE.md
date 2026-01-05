# Claims Management System - Setup Guide

## Quick Start

The application is **ready to use**! The database has been created and populated with test data.

### Starting the Application

**Option 1: Using the start script (Windows)**
```bash
start.bat
```

**Option 2: Manual start**
```bash
# Activate virtual environment
venv\Scripts\activate

# Start server
python manage.py runserver
```

### Access the Application

1. Open your browser
2. Navigate to: **http://127.0.0.1:8000/**
3. Login with any of the test users below

## Test Accounts

| Username | Password | Role | Capabilities |
|----------|----------|------|--------------|
| **admin** | admin123 | Administrator | Full system access, can manage all claims and users |
| **john.smith** | password123 | Write | Can create, edit, and manage claims |
| **jane.doe** | password123 | Write | Can create, edit, and manage claims |
| **bob.wilson** | password123 | Read + Export | Can view claims and export to Excel |
| **alice.brown** | password123 | Read Only | Can only view claims |

## What's Included

### Pre-loaded Data
- **5 test users** with different permission levels
- **15 sample claims** with various statuses:
  - Draft claims
  - Claims under review
  - Submitted claims
  - Settled claims
  - Rejected claims
- **Comments** on several claims
- Various voyage details, vessel names, and ports

### Features Available

1. **Dashboard**
   - View your claims statistics
   - Quick access to recent claims
   - Status overview

2. **Claims Management**
   - Create new claims (Write/Admin users only)
   - Edit draft claims
   - View claim details
   - Update claim status
   - Delete claims (limited permissions)

3. **Collaboration**
   - Add comments to claims
   - Upload documents (simulated - files saved locally)
   - Assign claims to analysts

4. **Reporting**
   - Filter claims by status and type
   - Search by claim number, vessel, or voyage
   - Export to Excel (Read+Export, Write, Admin users)

5. **Admin Panel**
   - Access at: http://127.0.0.1:8000/admin/
   - Login with: admin/admin123
   - Full database management interface

## Application Structure

### Key Files
- `manage.py` - Django management script
- `db.sqlite3` - SQLite database (already populated)
- `start.bat` - Quick start script for Windows
- `requirements.txt` - Python dependencies

### Directories
- `claims/` - Main application code
  - `models.py` - Database models (User, Claim, Comment, Document)
  - `views.py` - Application logic
  - `forms.py` - Form definitions
  - `templates/` - HTML templates
  - `management/commands/` - Custom management commands
- `claims_system/` - Django project settings
- `media/` - Uploaded documents storage
- `venv/` - Python virtual environment

## Testing the Application

### Test Scenario 1: Read Only User
1. Login as **alice.brown/password123**
2. View the dashboard - see statistics
3. Browse claims list
4. Click on a claim to view details
5. Notice: No create/edit buttons (read-only access)

### Test Scenario 2: Claims Analyst (Write Access)
1. Login as **john.smith/password123**
2. Click "New Claim" button
3. Fill in voyage details:
   - Vessel: MV Test Vessel
   - Voyage: V2024999
   - Ports, dates, etc.
4. Enter contract terms and claim amount
5. Save the claim
6. View created claim
7. Add a comment
8. Try uploading a document
9. Update the claim status

### Test Scenario 3: Export Functionality
1. Login as **bob.wilson/password123**
2. Go to Claims list
3. Click "Export" in the sidebar
4. Download Excel file with all claims data
5. Open the file to verify data export

### Test Scenario 4: Admin User
1. Login as **admin/admin123**
2. Access admin panel at http://127.0.0.1:8000/admin/
3. View all claims, users, comments
4. Edit any claim regardless of status
5. Create new users with different roles
6. Manage all system data

## Common Tasks

### Adding a New User
1. Login as admin
2. Go to admin panel
3. Click "Users" → "Add User"
4. Fill in details and select role
5. Save

### Resetting Database
If you want to start fresh:
```bash
# Delete the database
del db.sqlite3

# Remove migrations (optional)
del claims\migrations\0001_initial.py

# Recreate everything
python manage.py makemigrations
python manage.py migrate
python manage.py populate_dummy_data
```

### Adding More Test Data
```bash
python manage.py populate_dummy_data
```
This will add additional test claims and users.

## Role-Based Permissions

### READ
- View own claims
- View assigned claims
- View claim details
- Add comments

### READ + EXPORT
- All READ permissions
- Export claims to Excel

### WRITE
- All READ + EXPORT permissions
- Create new claims
- Edit draft claims
- Update claim status
- Upload documents
- Delete own draft claims

### ADMIN
- All WRITE permissions
- Edit any claim (any status)
- Delete any claim
- Access admin panel
- Manage users

## Status Workflow

Claims follow this workflow:

1. **Draft** → Initial creation, editable
2. **Under Review** → Being reviewed by team
3. **Submitted** → Formally submitted to counterparty
4. **Settled** → Claim successfully settled
5. **Rejected** → Claim rejected

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is already in use
# Try a different port:
python manage.py runserver 8080
```

### Database errors
```bash
# Reset migrations
python manage.py migrate --run-syncdb
```

### Missing dependencies
```bash
pip install -r requirements.txt
```

## Next Steps for Development

### Immediate Enhancements
1. Add file validation for document uploads
2. Implement email notifications
3. Add more detailed reporting
4. Create PDF export for individual claims

### Production Readiness
1. Switch from SQLite to PostgreSQL
2. Configure proper authentication (LDAP/SSO)
3. Set up file storage (Azure Blob/S3)
4. Implement audit logging
5. Add unit tests
6. Configure production settings
7. Set up HTTPS/SSL

### Integration Ideas
1. Connect to SharePoint for document management
2. Integrate with SQL Server for enterprise data
3. Add REST API for mobile apps
4. Connect to accounting systems
5. Implement automated email workflows

## Support

- Django Documentation: https://docs.djangoproject.com/
- Bootstrap Documentation: https://getbootstrap.com/docs/
- Check [README.md](README.md) for more details

## Security Notes

⚠️ **This is a development/prototype setup**

For production:
- Change the SECRET_KEY in settings.py
- Set DEBUG = False
- Configure ALLOWED_HOSTS
- Use environment variables for sensitive data
- Implement proper authentication
- Enable HTTPS
- Regular security updates

---

**Your Claims Management System is ready to use!**

Simply run `start.bat` or `python manage.py runserver` and open http://127.0.0.1:8000/
