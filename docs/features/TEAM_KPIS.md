# Team KPIs Feature Documentation

## Overview

The **Team KPIs** feature is a comprehensive dashboard designed exclusively for Team Leads and Administrators to monitor team performance, workload distribution, and claims resolution metrics.

---

## Access Control

### Who Can Access?
- **Team Lead** role users
- **Admin** role users

### Location in Navigation
- **Menu**: Claims System → Team KPIs (appears directly below Dashboard)
- **Icon**: Bar chart icon
- **URL**: `/team-kpis/`

---

## Main Features

### 1. **Team Overview Cards**
Four high-level KPI cards displaying:
- **Total Team Members**: Count of all WRITE, TEAM_LEAD, and ADMIN users
- **Total Voyages Assigned**: Sum of all voyages assigned across the team
- **Pending Claims**: Total claims in DRAFT, UNDER_REVIEW, or SUBMITTED status
- **Resolved Claims**: Total claims in SETTLED or REJECTED status

### 2. **Team Performance Overview Chart**
- **Type**: Horizontal bar chart
- **Data Displayed**:
  - Pending claims per team member (yellow/warning color)
  - Resolved claims per team member (green/success color)
- **Purpose**: Visual comparison of workload and performance across team members
- **Technology**: Chart.js library

### 3. **Individual Team Member Workload Table**
Comprehensive table showing detailed metrics for each team member:

| Column | Description |
|--------|-------------|
| **Team Member** | Name, username, and profile photo |
| **Role** | User role badge (WRITE, TEAM_LEAD, ADMIN) |
| **Assigned Voyages** | Number of voyages currently assigned |
| **Pending Claims** | Claims awaiting resolution (yellow badge) |
| **Resolved Claims** | Claims successfully settled or rejected (green badge) |
| **Total Claims** | Sum of all claims assigned to the user |
| **Resolution Rate** | Percentage progress bar showing resolved/total ratio |
| **Workload Status** | Color-coded badge: Idle (0), Light (1-5), Medium (6-15), Heavy (16+) |
| **Actions** | View profile and details buttons |

### 4. **Monthly Trend Chart**
- **Type**: Line chart with filled area
- **Time Period**: Last 6 months
- **Data Series**:
  - **Claims Resolved** (green line): Number of claims that moved to SETTLED/REJECTED status
  - **New Claims** (blue line): Number of claims created in that month
- **Purpose**: Track team productivity trends over time

### 5. **Month Filter**
- **Dropdown Selector**: Shows last 12 months
- **Filter Options**:
  - "All Time" (default)
  - Individual months (e.g., "January 2026", "December 2025")
- **Behavior**: When a month is selected, the pending/resolved claims counts are filtered to only show claims created in that month

### 6. **Team Member Details Modal**
Clicking the "View Details" (eye icon) button opens a modal with:
- **Profile Section**:
  - Large profile photo
  - Full name
  - Role
- **Assigned Voyages Table**:
  - Voyage number
  - Vessel name
  - Number of claims per voyage
  - Assignment status
  - Scrollable table (max height 300px)
- **Performance Summary**:
  - Total claims
  - Pending claims
  - Resolved claims
  - Resolution rate percentage

---

## Workload Status Indicators

The system automatically categorizes team members based on their workload:

| Status | Voyages Count | Badge Color | Meaning |
|--------|---------------|-------------|---------|
| **Idle** | 0 | Gray | No voyages assigned |
| **Light** | 1-5 | Green | Manageable workload |
| **Medium** | 6-15 | Yellow | Moderate workload |
| **Heavy** | 16+ | Red | High workload - may need support |

---

## Resolution Rate Calculation

The resolution rate is calculated as:

```
Resolution Rate = (Resolved Claims / Total Claims) × 100
```

Where:
- **Resolved Claims** = Claims with status SETTLED or REJECTED
- **Total Claims** = All claims assigned to the user

The rate is displayed as:
- **Progress bar**: Visual representation with green color
- **Percentage**: Numerical value (e.g., "75%")

---

## Data Filtering

### Month Filter Behavior
When a specific month is selected:
- **Applies to**: Individual team member statistics (pending/resolved counts)
- **Filter logic**: Claims are filtered by `created_at` date falling within the selected month
- **Does not affect**:
  - Team member count
  - Voyage assignments (shows current state)
  - Monthly trend chart (always shows last 6 months)

---

## Technical Implementation

### Backend Views
1. **`team_kpis(request)`** (claims/views.py:1253)
   - Main view rendering the Team KPIs page
   - Permission check: `user.is_team_lead()`
   - Queries all team members (WRITE, TEAM_LEAD, ADMIN roles)
   - Calculates statistics per team member
   - Generates monthly trend data for last 6 months
   - Context includes: team_members, team_stats, monthly_trend, available_months

2. **`team_member_details(request, user_id)`** (claims/views.py:1377)
   - AJAX endpoint for member details modal
   - Returns JSON with: name, role, profile_photo, voyages, claims stats
   - Permission check: `user.is_team_lead()`

### URL Routes
- `/team-kpis/` → Main dashboard page
- `/team-kpis/member/<user_id>/` → AJAX endpoint for member details

### Template
- **File**: `claims/templates/claims/team_kpis.html`
- **Extends**: `claims/base.html`
- **JavaScript Libraries**: Chart.js (loaded from CDN)

### Database Queries
- **Team Members**: `User.objects.filter(role__in=['WRITE', 'TEAM_LEAD', 'ADMIN'])`
- **Voyages Count**: Annotated using `Count('assigned_voyages', distinct=True)`
- **Claims Filtering**: Based on `assigned_to` user and optional month filter
- **Status Filtering**:
  - Pending: `status__in=['DRAFT', 'UNDER_REVIEW', 'SUBMITTED']`
  - Resolved: `status__in=['SETTLED', 'REJECTED']`

---

## User Experience Features

### Visual Design
- **Responsive Layout**: Works on desktop and tablet devices
- **Color Coding**:
  - Primary (Blue): Total metrics
  - Info (Light Blue): Assignments
  - Warning (Yellow): Pending items
  - Success (Green): Resolved items
  - Danger (Red): Heavy workload alerts
- **Icons**: Bootstrap Icons used throughout for visual clarity
- **Charts**: Interactive Chart.js visualizations with hover tooltips

### Interactive Elements
- **Print Button**: Print-friendly layout (hides buttons and modals)
- **Month Filter**: Auto-submit on selection change
- **View Profile Button**: Links to team member's profile page
- **View Details Button**: Opens AJAX-powered modal with detailed info
- **Sortable Table**: Team members sorted by voyages count (descending), then alphabetically

### Loading States
- **Modal Loading**: Shows spinner while fetching member details
- **Error Handling**: Displays error alert if AJAX request fails

---

## Use Cases

### 1. **Daily Workload Monitoring**
Team Lead checks the dashboard each morning to:
- Identify team members with heavy workload
- Find team members who are idle and can take new assignments
- Balance workload distribution across the team

### 2. **Performance Reviews**
Use the resolution rate and monthly trends to:
- Evaluate individual team member performance
- Identify top performers
- Provide data-driven feedback during 1-on-1s

### 3. **Monthly Reporting**
Select specific months to generate reports showing:
- Claims resolved per team member in a given month
- New claims intake for capacity planning
- Team productivity trends

### 4. **Resource Planning**
Use the workload status indicators to:
- Determine if team needs additional resources
- Identify if team has capacity for new projects
- Plan vacation coverage and backup assignments

### 5. **Reassignment Decisions**
When reassigning voyages:
- Check who has light workload
- Review resolution rates to assign to most effective analysts
- Balance experience levels across the team

---

## Future Enhancements (Potential)

1. **Export to Excel**: Export team KPIs table to Excel for offline analysis
2. **Custom Date Ranges**: Allow selecting arbitrary date ranges instead of just months
3. **Team Comparison**: Compare current month vs. previous month performance
4. **Individual Drilldown**: Click on a team member to see all their claims
5. **Notifications**: Alert Team Leads when workload becomes unbalanced
6. **Target Setting**: Set resolution rate targets per team member
7. **Time-to-Resolution**: Track average days from claim creation to settlement
8. **Ship Owner Breakdown**: Show claims by ship owner per team member
9. **Claim Value Metrics**: Track total USD value of claims managed per analyst
10. **Assignment History**: View reassignment patterns and frequency

---

## Performance Considerations

- **Queries Optimized**: Uses `select_related` and `prefetch_related` to minimize database queries
- **Aggregation**: Uses Django ORM aggregation for efficient counting
- **AJAX Loading**: Member details loaded on-demand to reduce initial page load
- **Chart Rendering**: Client-side rendering with Chart.js (no server-side processing)

---

## Security

- **Role-Based Access**: Only TEAM_LEAD and ADMIN roles can access
- **Permission Check**: Both views check `user.is_team_lead()` before proceeding
- **User Visibility**: Shows only team members (WRITE, TEAM_LEAD, ADMIN roles)
- **Data Isolation**: Each team member can only see data they're authorized to view

---

## Testing

To test the Team KPIs feature:

1. **Login as Team Lead or Admin**
2. **Navigate**: Click "Team KPIs" in the sidebar menu
3. **Verify Display**:
   - Check that all team members are listed
   - Verify statistics are accurate
   - Test month filter functionality
4. **Test Modal**:
   - Click "View Details" on a team member
   - Verify voyages and statistics load correctly
5. **Test Charts**:
   - Hover over chart bars/lines to see tooltips
   - Verify data matches table values

---

## Troubleshooting

### Team KPIs menu item not showing
- **Cause**: User does not have TEAM_LEAD or ADMIN role
- **Solution**: Update user role in Django admin or via user management

### No team members displayed
- **Cause**: No users with WRITE, TEAM_LEAD, or ADMIN roles
- **Solution**: Create users with appropriate roles

### Member details modal fails to load
- **Cause**: JavaScript error or network issue
- **Check**: Browser console for error messages
- **Verify**: URL `/team-kpis/member/<user_id>/` is accessible

### Charts not rendering
- **Cause**: Chart.js CDN not accessible
- **Check**: Network tab in browser developer tools
- **Solution**: Ensure internet connection for CDN access

### Month filter not working
- **Cause**: Date format mismatch
- **Check**: Ensure selected month is in YYYY-MM format
- **Verify**: URL parameter `?month=2026-01` is correct

---

## Related Documentation

- [User Roles Documentation](../project/USER_ROLES.md) - Details on role permissions
- [Claims Models](../project/MODELS.md) - Understanding claim status fields
- [Voyage Assignment](../features/VOYAGE_ASSIGNMENT.md) - How voyage assignment works

---

## API Endpoints

### GET /team-kpis/
**Description**: Main Team KPIs dashboard page
**Method**: GET
**Authentication**: Required (Team Lead or Admin)
**Query Parameters**:
- `month` (optional): YYYY-MM format (e.g., "2026-01")

**Response**: HTML page with team KPIs dashboard

---

### GET /team-kpis/member/{user_id}/
**Description**: AJAX endpoint for team member details
**Method**: GET
**Authentication**: Required (Team Lead or Admin)
**Path Parameters**:
- `user_id`: Integer ID of the user

**Response**: JSON
```json
{
  "name": "John Doe",
  "role": "Write",
  "profile_photo": "/media/profile_photos/john.jpg",
  "voyages": [
    {
      "voyage_number": "V-2026-001",
      "vessel_name": "PACIFIC LEADER",
      "claims_count": 3,
      "status": "ASSIGNED"
    }
  ],
  "total_claims": 15,
  "pending_claims": 5,
  "resolved_claims": 10,
  "resolution_rate": 67
}
```

---

**Document Version**: 1.0
**Last Updated**: January 2026
**Author**: System Documentation
**Target Audience**: Team Leads, Administrators, Developers
