# Claims Management & Tracking System

A Django-based web application for managing and tracking demurrage and post-deal claims in the shipping industry.

## Features

### User Management & Permissions
- **Role-Based Access Control**
  - READ: View claims only
  - READ+EXPORT: View and export claims to Excel
  - WRITE: Create, edit, and manage claims
  - TEAM_LEAD: Assign voyages, manage team members
  - ADMIN: Full system access

- **User Directory**
  - Browse all system users with cards or table view
  - Sort by name, date joined, voyages, or claims (ascending/descending)
  - Search by name, username, or email
  - Filter by role and department
  - Export user data to Excel (permission-based)

- **Custom Permissions**
  - `view_user_directory`: Control access to user directory
  - `export_users`: Control ability to export user data
  - Granular permission management via Django admin

- **User Profiles**
  - Profile photos
  - Dark mode preference
  - Department and contact information
  - Activity statistics (voyages assigned, claims handled)

### Claims Management
- **Voyage Assignment System**
  - Assign voyages to analysts
  - Team leads can assign to team members
  - Track assignment status (Unassigned, Assigned, Completed)
  - Reassignment capability

- **Claims Lifecycle**
  - Create, view, edit, and delete claims
  - Track voyage details and contract terms
  - Automatic demurrage calculations
  - Status workflow: Draft → Under Review → Submitted → Settled/Rejected
  - Payment status tracking
  - Time-barred claims detection

- **Optimistic Locking**
  - Prevent concurrent edit conflicts
  - Version control on claims and voyages
  - User-friendly conflict resolution

### Collaboration
- Add comments to claims
- Upload and manage documents (Charter Party, SOF, emails, etc.)
- Assign claims to analysts
- Track created by and assigned to users

### Dashboard & Analytics
- Personal dashboard with statistics
- Analytics page with ship owner breakdown
- Filter and search claims
- Payment status breakdown
- Time-barred claims tracking
- Export capabilities

### User Interface
- **Modern Navigation**
  - Collapsible sidebar with menu groups
  - Claims System, Ship Data, Port Activity sections
  - Future-ready placeholder sections

- **Top Navbar**
  - User profile dropdown
  - Dark/Light mode toggle with sun/moon icons
  - Quick access to profile and admin panel

- **Responsive Design**
  - Bootstrap 5.3 based
  - Mobile-friendly interface
  - Card and table view options
  - Intuitive sorting and filtering

### Error Handling & Testing
- Comprehensive error handling for database issues
- User-friendly error messages
- Optimistic locking for concurrent edits
- Test coverage for critical scenarios
- Data validation and integrity checks

## Tech Stack

- **Backend**: Python 3.11, Django 5.2.9
- **Database**: SQLite (development), ready for PostgreSQL/SQL Server
- **Frontend**: Bootstrap 5.3, Bootstrap Icons
- **File Processing**: openpyxl (Excel export), Pillow (image handling)

## Installation

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd claims-management-system
   ```

2. **Create and activate virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install django pillow openpyxl
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Load dummy data (optional but recommended)**
   ```bash
   python manage.py populate_dummy_data
   ```
   This creates:
   - 5 test users with different roles
   - 3 ship owners
   - 30 voyages with claims
   - Sample comments and documents

6. **Create superuser (if not using dummy data)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main app: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Test Users

The system comes with pre-populated test users (after running populate_dummy_data):

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| admin | admin123 | Admin | Full system access, all permissions |
| john.smith | password123 | Team Lead | Assign voyages, manage claims, view users |
| jane.doe | password123 | Write | Create and edit claims |
| mike.johnson | password123 | Write | Create and edit claims |
| sarah.williams | password123 | Team Lead | Assign voyages, manage claims |

**Note**: Admin users automatically receive all permissions including `view_user_directory` and `export_users`.

## User Permissions Guide

### Granting User Directory Access

1. Login as admin at `/admin/`
2. Navigate to **Users** under CLAIMS
3. Select the user to edit
4. Scroll to **User permissions** section
5. Add these permissions:
   - `Can view user directory` - Allows access to Users page
   - `Can export users to Excel` - Allows exporting user data
6. Save the user

**Tip**: Create groups (e.g., "HR Team", "Management") and assign permissions to groups for easier bulk management.

See [USER_PERMISSIONS_GUIDE.md](USER_PERMISSIONS_GUIDE.md) for detailed permission documentation.

## Key Features Explained

### User Directory Views

**Cards View** (Default):
- Visual card layout with profile photos
- Shows role, department, contact info
- Statistics for voyages and claims assigned

**Table View**:
- Compact table format
- Sortable columns
- Quick actions

**Sorting Options**:
- Name (A-Z or Z-A)
- Date Joined (newest or oldest first)
- Voyages (most or least)
- Claims (most or least)

### Voyage Assignment Workflow

1. Admin/Team Lead accesses Voyage Assignment
2. Unassigned voyages appear at the top
3. Click "Assign to Me" or "Assign to Analyst"
4. System tracks assignment status
5. Assigned analyst can create claims for the voyage
6. Reassignment available if needed

### Claim Status Workflow

```
Draft → Under Review → Submitted → Settled/Rejected
                              ↓
                    Payment Status tracked separately
```

### Dark Mode

Users can toggle between light and dark themes:
- Click sun/moon icon in top navbar
- Preference saved per user
- Applies across all pages

## Project Structure

```
claims-management-system/
├── claims/                          # Main Django app
│   ├── management/commands/         # Custom management commands
│   ├── migrations/                  # Database migrations
│   ├── templates/claims/            # HTML templates
│   │   ├── errors/                  # Error page templates
│   │   ├── claim_*.html            # Claim-related pages
│   │   ├── voyage_*.html           # Voyage-related pages
│   │   ├── user_*.html             # User-related pages
│   │   └── base.html               # Base template with navigation
│   ├── admin.py                     # Django admin configuration
│   ├── forms.py                     # Form definitions
│   ├── middleware.py                # Custom middleware (error handling)
│   ├── models.py                    # Database models
│   ├── urls.py                      # URL routing
│   └── views.py                     # View logic
├── claims_system/                   # Django project settings
├── media/                           # Uploaded files
│   ├── documents/                   # Claim documents
│   └── profile_photos/              # User profile photos
├── venv/                            # Virtual environment
├── db.sqlite3                       # SQLite database
├── manage.py                        # Django management script
├── README.md                        # This file
├── SETUP_GUIDE.md                   # Detailed setup instructions
├── TESTING_DOCUMENTATION.md         # Testing guide
├── USER_PERMISSIONS_GUIDE.md        # Permission management guide
└── TEAM_LEAD_ASSIGNMENT_FEATURES.md # Feature documentation
```

## Database Models

### Core Models

**User** (Extended AbstractUser):
- Role-based permissions
- Profile photo and bio
- Dark mode preference
- Department and contact info
- Custom permissions (view_user_directory, export_users)

**ShipOwner**:
- Owner name and code (from RADAR system)
- Contact information
- Active/inactive status

**Voyage**:
- RADAR voyage ID (unique)
- Vessel details
- Load/discharge ports and dates
- Assignment tracking
- Version control for optimistic locking

**Claim**:
- Voyage reference
- Contract terms (demurrage rate, laytime, etc.)
- Automatic calculations
- Status and payment tracking
- Time-barred flag
- Comments and documents
- Version control

**Comment & Document**:
- Attached to claims
- User tracking
- Timestamps

## Usage Examples

### Creating and Managing Claims

1. **Create Claim**
   - Navigate to assigned voyage
   - Click "Create Claim"
   - Fill in contract terms
   - System calculates demurrage automatically
   - Save as Draft

2. **Submit for Review**
   - Open claim detail page
   - Click "Update Status"
   - Change status to "Under Review"
   - Add comment explaining submission

3. **Track Payment**
   - Update payment status separately
   - Options: Not Sent, Sent, Partially Paid, Paid, Timebar

### Managing User Access

**View User Directory**:
- Only available to users with permission
- Click "Users" in sidebar (if you have access)
- Search, filter, and sort users
- Export to Excel (if you have export permission)

**Grant Permissions**:
- Admin → Users → Select user
- Add permissions or assign to groups
- Staff users bypass permission checks

## Development & Deployment

### Running Tests

```bash
# Run all tests
python manage.py test claims.tests

# Run specific test class
python manage.py test claims.tests.ConcurrencyTestCase

# Run with coverage
pip install coverage
coverage run --source='claims' manage.py test claims.tests
coverage report
coverage html
```

See [TESTING_DOCUMENTATION.md](TESTING_DOCUMENTATION.md) for comprehensive testing guide.

### Production Considerations

**Database**:
- Migrate from SQLite to PostgreSQL or SQL Server
- Configure connection pooling
- Set up regular backups

**Security**:
- Change SECRET_KEY
- Set DEBUG = False
- Configure ALLOWED_HOSTS
- Use environment variables for secrets
- Enable HTTPS
- Set up CSRF protection
- Regular security updates

**Performance**:
- Configure caching (Redis, Memcached)
- Optimize database queries
- Set up static file serving (CDN)
- Consider async task queue (Celery)

**Monitoring**:
- Error tracking (Sentry)
- Performance monitoring
- Audit logging
- User analytics

### Customization Guide

**Add New Field to Claim**:
1. Update `claims/models.py` → Claim model
2. Create migration: `python manage.py makemigrations`
3. Run migration: `python manage.py migrate`
4. Update `claims/forms.py` → ClaimForm
5. Update templates to display the field

**Add New Permission**:
1. Add to model's Meta.permissions
2. Create migration
3. Update views with permission checks
4. Update templates to show/hide based on permission

**Customize UI**:
- Edit `claims/templates/claims/base.html` for navigation
- Modify individual page templates
- Update CSS in `<style>` blocks or add static CSS files

## Troubleshooting

### Common Issues

**User can't see Users menu**:
- Check if user has `view_user_directory` permission
- Check if user is staff (`is_staff=True`)
- User may need to logout and login again

**Concurrent edit error**:
- Another user modified the record
- Reload the page to see latest changes
- Reapply your changes

**Permission denied errors**:
- Check user role and permissions
- Verify `is_staff` status for admin access
- Check migration status: `python manage.py showmigrations`

### Getting Help

1. Check error logs in console
2. Review Django documentation: https://docs.djangoproject.com/
3. Check migration status: `python manage.py showmigrations claims`
4. Verify database integrity: `python manage.py check`

## Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed installation and configuration
- **[TESTING_DOCUMENTATION.md](TESTING_DOCUMENTATION.md)** - Testing strategy and test cases
- **[USER_PERMISSIONS_GUIDE.md](USER_PERMISSIONS_GUIDE.md)** - Permission management
- **[TEAM_LEAD_ASSIGNMENT_FEATURES.md](TEAM_LEAD_ASSIGNMENT_FEATURES.md)** - Feature overview

## License

This is a prototype project for demonstration and internal use purposes.

## Version History

- **v1.3** (Dec 2025) - User directory with permissions, cards/table views, export
- **v1.2** (Dec 2025) - Voyage assignment, team lead features, optimistic locking
- **v1.1** (Dec 2025) - Analytics, dark mode, user profiles
- **v1.0** (Dec 2025) - Initial release with core claims management

---

**Last Updated**: December 27, 2025
