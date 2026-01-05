# Claims Management & Tracking System

A comprehensive Django-based web application for managing and tracking demurrage and post-deal claims in the maritime shipping industry, with integrated ship fleet management and port activity tracking.

## Features

### Multi-App Architecture
The system is organized into specialized Django apps for separation of concerns:
- **Claims App** - Core claims and voyage management
- **Ships App** - Ship master data and Time Charter fleet tracking
- **Port Activities App** - Port operations timeline with RADAR integration

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
- **RADAR System Integration** ⚠️
  - **Claims synced from RADAR system only** (creation/deletion disabled in UI)
  - Automatic sync of voyages and claims from RADAR
  - Users can update, comment, and manage existing claims
  - Ensures single source of truth and data consistency

- **Voyage Assignment System**
  - Assign voyages to analysts
  - Team leads can assign to team members
  - Track assignment status (Unassigned, Assigned, Completed)
  - Assignment history tracking with audit trail
  - Reassignment capability with reason tracking

- **Claims Lifecycle**
  - View and edit claims (creation via RADAR sync only)
  - Track voyage details and contract terms
  - Automatic demurrage calculations
  - Status workflow: Draft → Under Review → Submitted → Settled/Rejected
  - Payment status tracking with RADAR sync
  - Time-barred claims detection
  - Activity logging for all claim changes
  - Add comments and upload documents

- **Optimistic Locking**
  - Prevent concurrent edit conflicts
  - Version control on claims and voyages
  - User-friendly conflict resolution

### Ship Fleet Management (New)
- **Ship Master Data**
  - IMO number and vessel identification
  - Technical specifications (DWT, GT, engine power)
  - Vessel types (VLCC, Suezmax, Aframax, Panamax, MR, LR1, LR2, Handysize)
  - Charter type tracking (Spot, Time Charter, Bareboat)

- **Time Charter (TC) Fleet**
  - TC fleet flag and management
  - Charter period tracking (start/end dates)
  - Daily hire rate tracking
  - Charterer information
  - Charter status indicators (Active, Expiring, Inactive)
  - Days remaining calculations
  - External database sync support

- **Ship Admin Interface**
  - Visual TC status indicators with color coding
  - Expiry warnings (red: ≤30 days, orange: ≤90 days, green: >90 days)
  - Comprehensive filtering by vessel type, charter type, TC status
  - Cross-app integration with voyage and claim history

### Port Activity Tracking (New)
- **Activity Types**
  - Loading/Discharging operations
  - Ship-to-Ship (STS) transfers
  - Dry-docking
  - Off-hire periods
  - Bunkering
  - Waiting time
  - Custom activity categories

- **Timeline Management**
  - Start and end datetime tracking
  - **Estimated vs Actual dates** (independent for start and end)
  - RADAR system integration for date updates
  - Auto-calculated duration (days and hours)
  - Overlap validation to prevent double-booking

- **Port Information**
  - Port name (activity location)
  - Load port and discharge port fields
  - Cargo quantity tracking
  - Voyage and ship linkage

- **RADAR Integration**
  - RADAR activity ID tracking
  - Last sync timestamp
  - Automatic status updates (ESTIMATED → ACTUAL)
  - Mixed status support (e.g., start actual, end estimated)

- **Service Layer**
  - Business logic separation
  - Pivot table data: Ship → Voyage → Activities
  - Filter by activity category (STS, dry-dock, offhire)
  - Summary statistics by ship and activity type

### Data Integrity & Performance
- **Database Optimization**
  - 25+ strategic indexes for SQL Server deployment
  - Single-column indexes for lookups
  - Composite indexes for common query patterns
  - Query optimization with select_related/prefetch_related

- **Cloud Storage Preparation**
  - django-storages integration ready
  - Hierarchical file paths for documents
  - Support for Azure Blob Storage and AWS S3
  - Cloud storage path tracking on documents

- **Audit & Tracking**
  - Assignment history with VoyageAssignment model
  - Claim activity logs (creation, status changes, reassignments)
  - User tracking (created_by, assigned_to)
  - Timestamp tracking (created_at, updated_at)

### Collaboration
- Add comments to claims
- Upload and manage documents (Charter Party, SOF, emails, etc.)
- Assign claims to analysts
- Track created by and assigned to users
- Activity logs visible in admin interface

### Dashboard & Analytics
- Personal dashboard with statistics
- Analytics page with ship owner breakdown
- Charts and visualizations
- Filter and search claims
- Payment status breakdown
- Time-barred claims tracking
- Export capabilities

### User Interface
- **Modern Navigation**
  - Collapsible sidebar with menu groups
  - Claims System section
  - Ship Data section (Ships module)
  - Port Activity section (Activities tracking)

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
- **Database**: SQLite (development), optimized for SQL Server production
- **Frontend**: Bootstrap 5.3, Bootstrap Icons
- **File Processing**: openpyxl (Excel export), Pillow (image handling)
- **Cloud Storage**: django-storages (Azure Blob, AWS S3 ready)

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
   pip install -r requirements.txt
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
   - Test ships and port activities

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

## Project Structure

```
claims-management-system/
├── claims/                          # Core claims & voyage management
│   ├── management/commands/         # Custom management commands
│   ├── migrations/                  # Database migrations (10 files)
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
├── ships/                           # Ship fleet management (NEW)
│   ├── migrations/                  # Database migrations
│   ├── admin.py                     # Ship admin with TC status
│   ├── models.py                    # Ship model
│   └── apps.py                      # App configuration
├── port_activities/                 # Port activity tracking (NEW)
│   ├── migrations/                  # Database migrations
│   ├── admin.py                     # Activity admin with date indicators
│   ├── models.py                    # ActivityType, PortActivity models
│   ├── services.py                  # Business logic layer
│   └── apps.py                      # App configuration
├── claims_system/                   # Django project settings
│   ├── settings.py                  # Project configuration
│   ├── urls.py                      # Root URL configuration
│   └── wsgi.py                      # WSGI configuration
├── media/                           # Uploaded files
│   ├── documents/                   # Claim documents
│   └── profile_photos/              # User profile photos
├── venv/                            # Virtual environment
├── db.sqlite3                       # SQLite database
├── manage.py                        # Django management script
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── SETUP_GUIDE.md                   # Detailed setup instructions
├── TESTING_DOCUMENTATION.md         # Testing guide
├── USER_PERMISSIONS_GUIDE.md        # Permission management guide
├── TEAM_LEAD_ASSIGNMENT_FEATURES.md # Feature documentation
└── IMPROVEMENTS_LOG.md              # Change log
```

## Database Models

### Claims App Models

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
- Assignment tracking with history
- Version control for optimistic locking

**Claim**:
- Voyage reference
- Contract terms (demurrage rate, laytime, etc.)
- Automatic calculations
- Status and payment tracking
- Time-barred flag
- Comments and documents
- Version control
- Activity logging

**VoyageAssignment**:
- Assignment history tracking
- Assigned to/by users
- Assignment timestamps
- Duration calculations
- Reassignment reason

**ClaimActivityLog**:
- Action type (CREATED, STATUS_CHANGED, etc.)
- User who performed action
- Old and new values
- Timestamp tracking

**Comment & Document**:
- Attached to claims
- User tracking
- Cloud storage path support
- Timestamps

### Ships App Models (NEW)

**Ship**:
- IMO number (unique identifier)
- Vessel name and type
- Technical specifications (DWT, GT, engine)
- Charter information (type, dates, rates)
- TC fleet management fields
- External database sync support
- Properties: is_charter_active, charter_days_remaining

### Port Activities App Models (NEW)

**ActivityType**:
- Activity name and category
- Description
- Active/inactive status

**PortActivity**:
- Ship and voyage references (cross-app)
- Activity type
- Port information (port_name, load_port, discharge_port)
- Timeline with estimated/actual tracking:
  - start_datetime + start_date_status
  - end_datetime + end_date_status
- Auto-calculated duration
- Cargo quantity
- RADAR sync tracking
- Overlap validation
- Properties: duration_hours, duration_days, is_fully_actual, is_fully_estimated

## Key Features Explained

### Time Charter Fleet Management

**TC Status Indicators**:
- **Green**: Active charter, >90 days remaining
- **Orange**: Active charter, 31-90 days remaining
- **Red**: Expiring soon, ≤30 days remaining
- **Gray**: Inactive or not TC fleet

**Charter Tracking**:
- Automatic status calculation based on dates
- Days remaining display
- Daily hire rate tracking
- Charterer information
- Integration with voyage data

### Port Activity Timeline

**Estimated vs Actual Dates**:
- Independent status for start and end dates
- RADAR system updates from estimated to actual
- Mixed status support (e.g., start actual, end estimated)
- Visual indicators in admin (✓ for actual, ~ for estimated)
- Color-coded badges (green: actual, orange: estimated, gray: mixed)

**Activity Filtering**:
- Filter by category (STS, dry-dock, offhire, etc.)
- Ship timeline view
- Voyage activities grouping
- Date range filtering
- Pivot table structure: Ship → Voyage → Activities

**Business Logic Layer**:
- `PortActivityService.get_pivot_data()` - Hierarchical data
- `PortActivityService.get_sts_operations()` - STS filtering
- `PortActivityService.get_drydock_operations()` - Dry-dock filtering
- `PortActivityService.get_offhire_periods()` - Offhire filtering

### Assignment History Tracking

**Voyage Assignment History**:
- Full audit trail of all assignments
- Assigned to/by user tracking
- Assignment and unassignment timestamps
- Duration calculations
- Reassignment reason notes
- Active/completed status
- Visible in voyage detail page

### Optimistic Locking & Concurrency

**Version Control**:
- Claims and voyages have version fields
- Prevents lost updates in concurrent edits
- User-friendly error messages
- Reload and retry mechanism

### Cloud Storage Integration

**Document Management**:
- Hierarchical file paths (YYYY/MM/)
- Cloud storage path tracking
- django-storages ready
- Azure Blob and AWS S3 support
- Local development with file system

## Usage Examples

### Managing Time Charter Fleet

1. **Add TC Vessel**
   - Navigate to Ships in admin
   - Click "Add Ship"
   - Fill in vessel details and IMO
   - Set charter type to "Time Charter"
   - Mark "Is TC fleet" checkbox
   - Enter charter dates and daily rate
   - Enter charterer name
   - Save

2. **Monitor Charter Expiry**
   - View ships list in admin
   - Check TC Status column for color-coded alerts
   - Red vessels require attention (≤30 days)
   - Plan renewals or replacements

### Tracking Port Activities

1. **Create Port Activity**
   - Navigate to Port Activities in admin
   - Click "Add Port Activity"
   - Select ship and voyage
   - Choose activity type (e.g., Loading)
   - Enter port names (load/discharge if applicable)
   - Set start/end datetimes
   - Mark dates as ESTIMATED or ACTUAL
   - Enter cargo quantity if applicable
   - Save

2. **Update from RADAR**
   - RADAR sync updates date statuses
   - Estimated dates become actual when confirmed
   - Last sync timestamp recorded
   - Visual indicators update automatically

3. **View Ship Timeline**
   - Use `PortActivityService.get_ship_timeline()`
   - See all activities chronologically
   - Filter by date range
   - Identify overlaps or gaps

4. **Filter by Activity Type**
   - STS operations: `get_sts_operations()`
   - Dry-dock periods: `get_drydock_operations()`
   - Offhire periods: `get_offhire_periods()`

## Development & Deployment

### Testing

**Test Coverage: 44.69%** (Target: 70%)
- **292 passing tests** across 8 test files
- Comprehensive test suite covering models, views, APIs, and services

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=claims --cov=ships --cov=port_activities --cov-report=term-missing

# Run specific test file
pytest claims/test_views.py -v

# Generate HTML coverage report
pytest --cov=claims --cov=ships --cov=port_activities --cov-report=html
open htmlcov/index.html
```

**Documentation**:
- [Testing Guide](docs/development/TESTING.md) - Comprehensive testing guide and best practices
- [Coverage Report](docs/development/TEST_COVERAGE_REPORT.md) - Detailed coverage analysis and roadmap
- [What Are Tests?](docs/project/WHAT_ARE_TESTS.md) - Simple explanation for non-developers

### Production Considerations

**Database**:
- Migrate from SQLite to SQL Server or PostgreSQL
- Database already optimized with 40+ indexes
- Configure connection pooling
- Set up regular backups

**Cloud Storage**:
- Configure django-storages settings
- Set up Azure Blob Storage or AWS S3
- Update MEDIA_URL and MEDIA_ROOT
- Migrate existing files

**Security**:
- Change SECRET_KEY
- Set DEBUG = False
- Configure ALLOWED_HOSTS
- Use environment variables for secrets
- Enable HTTPS
- Set up CSRF protection
- Regular security updates

**Performance**:
- Database indexes already implemented
- Query optimization with select_related/prefetch_related
- Configure caching (Redis, Memcached)
- Set up static file serving (CDN)
- Consider async task queue (Celery) for RADAR sync

**Integration**:
- RADAR system API integration
- External TC fleet database sync
- Email notifications for charter expiry
- Automated activity updates

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

**Ship or Port Activity not showing**:
- Verify migrations are applied: `python manage.py migrate`
- Check if apps are in INSTALLED_APPS
- Restart development server

### Getting Help

1. Check error logs in console
2. Review Django documentation: https://docs.djangoproject.com/
3. Check migration status: `python manage.py showmigrations`
4. Verify database integrity: `python manage.py check`

## Documentation

### Quick Links
- **[README.md](README.md)** - This file, project overview
- **[SETUP_GUIDE](docs/setup/SETUP_GUIDE.md)** - Installation and configuration
- **[TESTING](docs/development/TESTING.md)** - Testing guide and best practices
- **[API Guide](docs/api/API_GUIDE.md)** - REST API documentation
- **[CHANGELOG](docs/project/CHANGELOG.md)** - Version history and improvements

### Setup & Configuration
- [docs/setup/SETUP_GUIDE.md](docs/setup/SETUP_GUIDE.md) - Detailed installation instructions
- [docs/setup/SECURITY_SETUP.md](docs/setup/SECURITY_SETUP.md) - Security configuration

### Features & User Guides
- [docs/features/TEAM_LEAD_ASSIGNMENT_FEATURES.md](docs/features/TEAM_LEAD_ASSIGNMENT_FEATURES.md) - Team lead features
- [docs/features/USER_PERMISSIONS_GUIDE.md](docs/features/USER_PERMISSIONS_GUIDE.md) - Permission system
- [docs/features/NEW_FEATURES_GUIDE.md](docs/features/NEW_FEATURES_GUIDE.md) - Latest features

### Development
- [docs/development/TESTING.md](docs/development/TESTING.md) - Testing guide (292 tests, 44.69% coverage)
- [docs/development/TEST_COVERAGE_REPORT.md](docs/development/TEST_COVERAGE_REPORT.md) - Coverage analysis and roadmap
- [docs/development/TYPE_HINTS_AND_CBV_SUMMARY.md](docs/development/TYPE_HINTS_AND_CBV_SUMMARY.md) - Code style guide
- [docs/development/IMPLEMENTATION_GUIDE.md](docs/development/IMPLEMENTATION_GUIDE.md) - Implementation patterns

### API Documentation
- [docs/api/API_GUIDE.md](docs/api/API_GUIDE.md) - REST API reference and usage

### Project Status
- [docs/project/STATUS.md](docs/project/STATUS.md) - Current status and improvements
- [docs/project/CHANGELOG.md](docs/project/CHANGELOG.md) - Complete version history

## License

This is a prototype project for demonstration and internal use purposes.

## Version History

- **v2.0** (Dec 2025) - Multi-app architecture, Ships & Port Activities modules, performance optimization
- **v1.3** (Dec 2025) - User directory with permissions, cards/table views, export
- **v1.2** (Dec 2025) - Voyage assignment, team lead features, optimistic locking
- **v1.1** (Dec 2025) - Analytics, dark mode, user profiles
- **v1.0** (Dec 2025) - Initial release with core claims management

---

**Last Updated**: December 29, 2025
