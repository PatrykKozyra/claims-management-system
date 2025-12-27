# User Permissions Guide

## Overview

The Claims Management System now has custom permissions for accessing the User Directory and exporting user data to Excel.

## Available Permissions

### 1. **Can view user directory** (`claims.view_user_directory`)
- **Purpose**: Controls access to the Users page
- **Default**: Granted to all staff users and ADMIN role users
- **Effect**:
  - Users WITH this permission can see the "Users" menu item
  - Users WITH this permission can access `/users/`
  - Users WITHOUT this permission cannot view the user directory

### 2. **Can export users to Excel** (`claims.export_users`)
- **Purpose**: Controls ability to export user data to Excel
- **Default**: Granted to all staff users and ADMIN role users
- **Effect**:
  - Users WITH this permission see the "Export to Excel" button on the Users page
  - Users WITH this permission can download user data as Excel file
  - Users WITHOUT this permission cannot export user data

## How to Grant Permissions

### Method 1: Django Admin Interface

1. **Login as admin** at `/admin/`
2. **Navigate to Users**: Click on "Users" under "CLAIMS"
3. **Select a user** to edit
4. **Scroll to "User permissions" section**
5. **Add permissions**:
   - Search for "Can view user directory"
   - Search for "Can export users to Excel"
   - Move them from "Available permissions" to "Chosen permissions"
6. **Save** the user

### Method 2: Using Groups (Recommended for bulk assignment)

1. **Create a group** (e.g., "HR Team", "Management")
2. **Assign permissions to the group**:
   - Can view user directory
   - Can export users to Excel
3. **Add users to the group**

This way, all users in the group automatically get these permissions.

### Method 3: Programmatically (for developers)

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

# Get the user
user = User.objects.get(username='john.doe')

# Get the permissions
view_perm = Permission.objects.get(codename='view_user_directory')
export_perm = Permission.objects.get(codename='export_users')

# Grant permissions
user.user_permissions.add(view_perm, export_perm)
```

## Permission Hierarchy

### Who has access by default:

1. **Staff users** (`is_staff=True`):
   - Automatically bypass permission checks
   - Can always view user directory
   - Can always export users

2. **ADMIN role users** (`role='ADMIN'`):
   - Automatically granted both permissions via migration
   - Should typically also have `is_staff=True`

3. **Other users**:
   - Must be explicitly granted permissions
   - No access by default

## Use Cases

### Scenario 1: HR Team Member
**Needs**: View user directory, export user data
**Solution**:
- Create "HR Team" group
- Assign both permissions to the group
- Add HR team members to the group

### Scenario 2: Team Lead
**Needs**: View user directory only (to see team members)
**Solution**:
- Grant only `view_user_directory` permission
- Do NOT grant `export_users` permission

### Scenario 3: Regular Claims Analyst
**Needs**: No access to user directory
**Solution**:
- Do NOT grant any user directory permissions
- Users menu item will not appear
- Cannot access `/users/` URL

## Security Notes

- ✅ Permissions are checked both in views and templates
- ✅ URL access is protected even if user guesses the URL
- ✅ Export button only shows if user has export permission
- ✅ Menu item only shows if user has view permission
- ✅ Staff users always bypass these checks (Django default behavior)

## Checking Permissions in Code

### In Views
```python
# Check if user has permission
if request.user.has_perm('claims.view_user_directory'):
    # User can view
    pass

# Check if user is staff (bypasses permission check)
if request.user.is_staff:
    # Staff can do anything
    pass
```

### In Templates
```django
{% if perms.claims.view_user_directory or user.is_staff %}
    <!-- Show users menu -->
{% endif %}

{% if perms.claims.export_users or user.is_staff %}
    <!-- Show export button -->
{% endif %}
```

## Troubleshooting

### User cannot see Users menu
**Check**:
1. Is user staff? (`is_staff=True`)
2. Does user have `view_user_directory` permission?
3. Has user logged out and back in after permission change?

### User cannot export
**Check**:
1. Is user staff? (`is_staff=True`)
2. Does user have `export_users` permission?
3. Does user also have `view_user_directory`? (required to access the page)

### Permission not appearing in admin
**Check**:
1. Run migrations: `python manage.py migrate`
2. Check Django's permission system is working
3. Look for the permission in admin under Auth > Permissions

## Migration History

- **0005_alter_user_options.py**: Added custom permissions to User model
- **0006_grant_admin_user_permissions.py**: Automatically granted permissions to existing staff and admin users

---

**Last Updated**: 2025-12-27
