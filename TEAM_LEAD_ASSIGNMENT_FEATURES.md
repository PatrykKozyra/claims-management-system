# Team Lead Assignment & Reassignment Features

## Overview

New features have been added to support team lead management of voyage and claim assignments, including the ability to reassign voyages when analysts go on unexpected leave.

---

## New Features Implemented

### 1. ✅ Team Lead Role

**Added a new role**: `TEAM_LEAD`

**Role Hierarchy**:
- `READ` - Read-only access
- `READ_EXPORT` - Read + Export capabilities
- `WRITE` - Can write/edit claims and self-assign voyages
- `TEAM_LEAD` - Can assign voyages to any analyst + all WRITE permissions
- `ADMIN` - Full administrative access

**Permissions**:
- Team Leads can:
  - Assign unassigned voyages to any analyst
  - Reassign assigned voyages to different analysts
  - All capabilities of WRITE role
  - Export data
- Regular analysts (WRITE role) can:
  - Self-assign unassigned voyages
  - Reassign their own voyages to others
  - Cannot assign voyages to other analysts initially

---

### 2. ✅ Team Lead Assignment Workflow

**Location**: Voyage Assignment page (`/voyages/`)

**How it Works**:

#### For Team Leads:
- Unassigned voyages show a **dropdown** with all active analysts
- Select an analyst from the dropdown
- Click "Assign" button
- Voyage and ALL claims are assigned to the selected analyst
- Success message confirms assignment

#### For Regular Analysts:
- Unassigned voyages show the original **"Assign to Me"** button
- Click the button to self-assign
- Voyage and ALL claims are assigned to themselves

**Screenshot Reference**:
```
Team Lead View:
[Select Analyst ▼] [Assign]

Regular Analyst View:
[Assign to Me]
```

---

### 3. ✅ Reassignment Functionality

**Location**: Voyage Detail page (`/voyages/<id>/`)

**Who Can Reassign**:
1. **Team Leads** - Can reassign any voyage
2. **Admins** - Can reassign any voyage
3. **Assigned Analyst** - Can reassign their own voyage

**How it Works**:

1. On voyage detail page, assigned voyages show a **"Reassign"** button
2. Click "Reassign" to open a modal dialog
3. Fill in the form:
   - **Select New Analyst** (required) - Dropdown of all active analysts except current one
   - **Reason for Reassignment** (required) - Text area for explanation
4. Click "Reassign Voyage"
5. System performs:
   - Reassigns voyage to new analyst
   - Reassigns ALL claims to new analyst
   - Adds a comment to each claim with reassignment details
   - Shows success message

**Use Cases**:
- Analyst goes on unexpected leave
- Workload redistribution
- Skill-based assignment changes
- Vacation coverage

**Example Reassignment Comment**:
```
Reassigned from John Smith to Jane Doe.
Reason: Extended sick leave - requires immediate coverage
```

---

## Technical Implementation

### Database Changes

**Migration**: `claims/migrations/0003_alter_user_role.py`

**Changes**:
- Updated `User.role` field choices to include `TEAM_LEAD`

### New Model Methods

**File**: `claims/models.py`

```python
def is_team_lead(self):
    """Check if user has team lead or admin role"""
    return self.role in ['TEAM_LEAD', 'ADMIN']

def can_assign_voyages(self):
    """Check if user can assign voyages to others"""
    return self.role in ['TEAM_LEAD', 'ADMIN']
```

**Updated Methods**:
- `can_export()` - Now includes TEAM_LEAD
- `can_write()` - Now includes TEAM_LEAD

### New Views

**File**: `claims/views.py`

#### 1. `voyage_assign_to(request, pk)`
- Team lead assignment view
- Assigns voyage to specified analyst
- Permission: `user.can_assign_voyages()`
- POST only

#### 2. `voyage_reassign(request, pk)`
- Reassignment view for handling analyst changes
- Permission: Team lead, admin, or currently assigned analyst
- Creates comment on all claims with reason
- POST only

### New URLs

**File**: `claims/urls.py`

```python
path('voyages/<int:pk>/assign-to/', views.voyage_assign_to, name='voyage_assign_to'),
path('voyages/<int:pk>/reassign/', views.voyage_reassign, name='voyage_reassign'),
```

### Template Updates

#### `voyage_list.html`
**Changes**:
- Conditional rendering based on `user.can_assign_voyages()`
- Team leads see dropdown + "Assign" button
- Regular analysts see "Assign to Me" button
- Updated help text to explain team lead functionality

#### `voyage_detail.html`
**Changes**:
- Added "Reassign" button to assigned voyage alert
- Added reassignment modal with form:
  - Analyst dropdown (excludes current analyst)
  - Reason textarea (required)
  - Warning about affecting all claims
- Modal only visible to authorized users

---

## User Testing Guide

### Test Account Credentials

```
sarah.teamlead / password123    (Team Lead)
john.analyst / password123      (Senior Analyst - WRITE)
jane.analyst / password123      (Analyst - WRITE)
mike.analyst / password123      (Junior Analyst - WRITE)
admin / admin123                (Administrator)
```

### Test Scenario 1: Team Lead Assignment

**Goal**: Team lead assigns unassigned voyage to analyst

**Steps**:
1. Login as `sarah.teamlead / password123`
2. Navigate to "Voyage Assignment" page
3. Find an UNASSIGNED voyage (yellow highlighted row)
4. Select "John Smith" from the dropdown
5. Click "Assign" button
6. Verify success message
7. Verify voyage is now assigned to John
8. Open the voyage detail page
9. Check that all claims are assigned to John

**Expected Result**: ✅ Voyage and all claims assigned to John Smith

### Test Scenario 2: Regular Analyst Self-Assignment

**Goal**: Regular analyst assigns themselves to voyage

**Steps**:
1. Login as `john.analyst / password123`
2. Navigate to "Voyage Assignment" page
3. Find an UNASSIGNED voyage
4. Should see "Assign to Me" button (NOT dropdown)
5. Click "Assign to Me"
6. Verify voyage assigned to self

**Expected Result**: ✅ Self-assignment works, no dropdown visible

### Test Scenario 3: Reassignment Due to Leave

**Goal**: Reassign analyst's voyages when they go on leave

**Steps**:
1. Login as `sarah.teamlead / password123`
2. Navigate to "Voyage Assignment"
3. Filter by "Analyst: John Smith"
4. Open any assigned voyage
5. Click "Reassign" button
6. Select "Jane Doe" from dropdown
7. Enter reason: "Extended sick leave - requires immediate coverage"
8. Click "Reassign Voyage"
9. Verify success message
10. Check voyage detail - should show Jane as assigned
11. Open a claim from that voyage
12. Scroll to comments - should see reassignment comment

**Expected Result**: ✅ Voyage reassigned, all claims reassigned, comment added

### Test Scenario 4: Analyst Self-Reassignment

**Goal**: Analyst reassigns their own voyage

**Steps**:
1. Login as `john.analyst / password123`
2. Go to "Voyage Assignment" page
3. Filter "Analyst: My Voyages"
4. Open any of your assigned voyages
5. Should see "Reassign" button
6. Click "Reassign"
7. Select another analyst
8. Enter reason: "Going on vacation next week"
9. Submit
10. Verify reassignment successful

**Expected Result**: ✅ Analyst can reassign their own voyages

### Test Scenario 5: Permission Validation

**Goal**: Verify analysts cannot assign to others initially

**Steps**:
1. Login as `mike.analyst / password123`
2. Navigate to "Voyage Assignment"
3. Find UNASSIGNED voyage
4. Should see "Assign to Me" button only
5. Should NOT see analyst dropdown

**Expected Result**: ✅ No dropdown visible for regular analysts

---

## Business Logic

### Auto-Assignment Flow

When a voyage is assigned (team lead or self-assignment):
1. Voyage `assignment_status` → `ASSIGNED`
2. Voyage `assigned_analyst` → Selected analyst
3. Voyage `assigned_at` → Current timestamp
4. **ALL existing claims** → `assigned_to` = Selected analyst
5. **ALL future claims** → Auto-assigned via `Claim.save()` method

### Reassignment Flow

When a voyage is reassigned:
1. Previous analyst saved for reference
2. Voyage reassigned to new analyst (calls `voyage.assign_to()`)
3. All claims automatically reassigned via model method
4. Comment created on each claim:
   - User: Person who initiated reassignment
   - Content: "Reassigned from [Old] to [New]. Reason: [Reason]"
5. Success message displayed

---

## Permission Matrix

| Action | READ | READ_EXPORT | WRITE | TEAM_LEAD | ADMIN |
|--------|------|-------------|-------|-----------|-------|
| View voyages | ✅ | ✅ | ✅ | ✅ | ✅ |
| Self-assign voyage | ❌ | ❌ | ✅ | ✅ | ✅ |
| Assign voyage to others | ❌ | ❌ | ❌ | ✅ | ✅ |
| Reassign own voyage | ❌ | ❌ | ✅ | ✅ | ✅ |
| Reassign any voyage | ❌ | ❌ | ❌ | ✅ | ✅ |
| Export data | ❌ | ✅ | ✅ | ✅ | ✅ |
| Edit user roles | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## UI/UX Notes

### Visual Differences

**Team Lead View** (Voyage List):
- Dropdown with analyst names
- Green "Assign" button
- Help text: "Team Lead: You can assign voyages to any analyst using the dropdown"

**Regular Analyst View** (Voyage List):
- Blue "Assign to Me" button
- Standard help text

**Reassignment Modal**:
- Warning alert about affecting all claims
- Required fields marked with red asterisk
- Current analyst shown below dropdown for reference
- Reason will be added to all claims as comment

### Accessibility

- All forms have proper labels
- Required fields clearly marked
- Color-coded buttons (primary, success, warning)
- Modal dialogs use Bootstrap accessibility features
- Success/error messages via Django messages framework

---

## Files Modified/Created

### Modified Files

1. **`claims/models.py`**
   - Added `TEAM_LEAD` to role choices
   - Added `is_team_lead()` method
   - Added `can_assign_voyages()` method
   - Updated `can_export()` and `can_write()` methods

2. **`claims/views.py`**
   - Added `voyage_assign_to()` view
   - Added `voyage_reassign()` view
   - Updated `voyage_detail()` to pass analysts list

3. **`claims/urls.py`**
   - Added `/voyages/<id>/assign-to/` route
   - Added `/voyages/<id>/reassign/` route

4. **`claims/templates/claims/voyage_list.html`**
   - Conditional assignment UI based on role
   - Team lead dropdown vs analyst button

5. **`claims/templates/claims/voyage_detail.html`**
   - Added "Reassign" button
   - Added reassignment modal dialog

6. **`claims/management/commands/simulate_radar_import.py`**
   - Added team lead user creation
   - Updated login credentials in summary

### Created Files

1. **`claims/migrations/0003_alter_user_role.py`**
   - Migration for TEAM_LEAD role

2. **`TEAM_LEAD_ASSIGNMENT_FEATURES.md`** (this file)
   - Feature documentation

---

## API Endpoints

### POST `/voyages/<id>/assign-to/`
**Purpose**: Team lead assigns voyage to specific analyst

**Parameters**:
- `analyst_id` (required) - User ID of analyst to assign

**Permission**: `user.can_assign_voyages()`

**Response**: Redirect to voyage list with success message

**Side Effects**:
- Voyage assigned to analyst
- All claims assigned to analyst

---

### POST `/voyages/<id>/reassign/`
**Purpose**: Reassign voyage to different analyst

**Parameters**:
- `new_analyst_id` (required) - User ID of new analyst
- `reassignment_reason` (required) - Text explanation

**Permission**: Team lead, admin, or currently assigned analyst

**Response**: Redirect to voyage detail with success message

**Side Effects**:
- Voyage reassigned to new analyst
- All claims reassigned to new analyst
- Comment added to all claims with reason

---

## Error Handling

### Validation Checks

1. **Assignment Permission**
   - Error if user doesn't have `can_assign_voyages()`
   - Error message: "You do not have permission to assign voyages to others"

2. **Analyst Selection**
   - Error if no analyst selected
   - Error message: "Please select an analyst"

3. **Analyst Capabilities**
   - Error if selected analyst doesn't have WRITE permissions
   - Error message: "[Name] does not have permission to handle claims"

4. **Reassignment Permission**
   - Error if user is not team lead/admin/current analyst
   - Error message: "You do not have permission to reassign this voyage"

5. **Reassignment Reason**
   - Required field in modal
   - HTML5 validation

---

## Future Enhancements

Potential improvements for consideration:

1. **Bulk Reassignment**
   - Reassign all voyages from one analyst to another
   - Useful for permanent role changes

2. **Temporary Assignment**
   - Set assignment with end date
   - Auto-reassign after vacation period

3. **Assignment History**
   - Track all assignments/reassignments
   - Show timeline on voyage detail page

4. **Workload Balancing**
   - Show analyst workload (number of assigned voyages/claims)
   - Suggest least-loaded analyst

5. **Assignment Notifications**
   - Email notification when assigned to new voyage
   - Email notification when voyage is reassigned

6. **Team Management**
   - Team leads can only assign within their team
   - Department-based filtering

---

## Troubleshooting

### Issue: Dropdown not showing for team lead

**Cause**: User role not set to TEAM_LEAD

**Solution**:
```bash
./venv/Scripts/python manage.py shell
>>> from claims.models import User
>>> user = User.objects.get(username='sarah.teamlead')
>>> user.role = 'TEAM_LEAD'
>>> user.save()
```

### Issue: Reassignment button not visible

**Cause**:
- User is not team lead/admin/assigned analyst
- Voyage is unassigned

**Solution**: Check user permissions and voyage assignment status

### Issue: Claims not auto-assigning

**Cause**: `Claim.save()` method not triggering

**Solution**: Verify `voyage.assign_to()` method is being called, not direct field assignment

---

## Summary

All requested features have been successfully implemented:

✅ **Team Lead Role** - New role with assignment permissions
✅ **Team Lead Assignment** - Dropdown to assign voyages to any analyst
✅ **Self-Assignment** - Regular analysts can still assign to themselves
✅ **Reassignment Functionality** - Handle unexpected leave situations
✅ **Reason Tracking** - Comments added to all claims with reassignment reason
✅ **Permission System** - Proper authorization checks throughout
✅ **Test User Created** - sarah.teamlead / password123

The system now supports flexible workforce management with proper permissions and tracking!

---

**Server**: http://127.0.0.1:8001/

**New User**: sarah.teamlead / password123 (Team Lead)
