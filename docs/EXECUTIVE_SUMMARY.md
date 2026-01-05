# Executive Summary: Claims Management System

## What Is This System?

A modern, web-based application designed to replace the current Qlik Sense/Vizlib Writeback solution for managing maritime claims and vessel operations. Built specifically for teams in Krakow and London who handle demurrage claims, vessel tracking, and port activities.

---

## Main Functionalities

### 1. **Claims Management**
- Track all demurrage and post-deal claims in one place
- Automatic calculations based on contract terms
- Monitor claim status from draft to settlement
- See payment tracking with automatic updates
- Flag claims that are approaching time limits
- Add notes and discussions on any claim
- Attach supporting documents (contracts, emails, statements of facts)

### 2. **Voyage & Assignment Tracking**
- Automatically sync voyage data from RADAR system
- Assign voyages to team members with full history
- See who is working on what, and for how long
- Track reassignments with reasons documented
- Personal dashboard showing your current workload

### 3. **Fleet Management**
- Maintain vessel master data (ship names, IMO numbers, specifications)
- Track time charter contracts with expiry alerts
  - Green: More than 90 days remaining
  - Orange: 31-90 days remaining
  - Red: 30 days or less (urgent attention needed)
- Store detailed vessel specifications for quick reference

### 4. **Port Activity Timeline**
- Record loading, discharging, dry-docking, and other port activities
- Track estimated vs. actual dates
- Automatic duration calculations
- Sync activity updates from RADAR
- View complete activity history for any vessel

### 5. **Reporting & Analytics**
- Personal statistics dashboard (your voyages and claims)
- Company-wide analytics (for team leads and admins)
- Export claims data to Excel for further analysis
- View claims by ship owner, payment status, and time limits
- Charts and visualizations for quick insights

### 6. **User Management**
- Five role levels: Read-Only, Read+Export, Write, Team Lead, and Admin
- Each user has their own profile with permissions
- Team leads can assign work to their team members
- Secure login with session management

---

## Key Benefits vs. Current Qlik Sense/Vizlib Writeback Solution

### **Performance Issues - SOLVED**

| Current Problem | New Solution |
|----------------|--------------|
| **Freezing and lagging with 50 users** | Built to handle 50+ concurrent users smoothly with modern web architecture |
| **Slow response times** | Optimized database with 40+ performance indexes for instant loading |
| **System crashes during peak usage** | Enterprise-grade infrastructure with proper session management |

### **Usability Issues - SOLVED**

| Current Problem | New Solution |
|----------------|--------------|
| **Lots of manual clicking** | Automatic data sync from RADAR - no manual data entry |
| **Difficult to track changes** | Full activity log showing who changed what and when |
| **No collaboration features** | Built-in comments system for team discussions on claims |
| **Limited visibility** | Personal dashboards showing your work and team progress |
| **Hard to find information** | Smart filtering and search across all data |

### **Functionality Issues - SOLVED**

| Current Problem | New Solution |
|----------------|--------------|
| **Limited to basic table editing** | Complete claims workflow with status tracking |
| **No document storage** | Upload and attach documents directly to claims |
| **No assignment tracking** | Full assignment history with reassignment reasons |
| **No alerts or notifications** | Visual indicators for urgent items (time-barred claims, expiring charters) |
| **Manual calculations** | Automatic demurrage calculations based on contract terms |
| **Can't track payment status** | Payment tracking with RADAR synchronization |
| **No audit trail** | Complete history of all changes with user tracking |

### **Data Management Issues - SOLVED**

| Current Problem | New Solution |
|----------------|--------------|
| **Data scattered across multiple sheets** | Single integrated database with all information connected |
| **Risk of data conflicts with multiple editors** | Automatic conflict prevention when two people edit the same claim |
| **No data validation** | Built-in validation rules to prevent errors |
| **Limited export options** | Role-based Excel export with customizable reports |

### **Security & Control Issues - SOLVED**

| Current Problem | New Solution |
|----------------|--------------|
| **Limited access control** | Five distinct role levels with granular permissions |
| **Can't restrict what users see** | Role-based access - users only see what they're allowed to |
| **No user activity tracking** | Complete logging of who did what and when |
| **Security vulnerabilities** | Enterprise-level security with rate limiting, session protection, and secure file uploads |

---

## Why This Matters for Your Team

### **For Analysts:**
- Spend less time clicking and more time analyzing
- Never lose track of your assigned voyages
- Quick access to all claim information in one place
- Collaborate with comments instead of emails
- Personal dashboard shows your workload at a glance

### **For Team Leads:**
- Easily assign and reassign work to your team
- See team workload and progress in real-time
- Generate reports for management quickly
- Track team performance and claim settlement rates
- Get alerts for urgent items (time-barred claims)

### **For Management:**
- Real-time visibility into all claims and their status
- Analytics dashboard showing key metrics
- No more system crashes during important presentations
- Secure, auditable system for compliance
- Export data for board reports instantly

---

## Deployment Plan

### **Infrastructure: Azure Virtual Machine in Europe**

**Location:** Azure Europe Region (optimized for your team locations)
- **90% of users in Krakow, Poland**
- **10% of users in London, UK**

**Technology Stack:**
- **Nginx:** Fast web server handling user requests
- **Gunicorn:** Application server running the system
- **SQL Server:** Enterprise database for reliable data storage
- **Azure Blob Storage:** Secure cloud storage for documents

**Expected Performance:**
- **Fast loading times:** European server location means low latency for all users
- **Reliable uptime:** Enterprise-grade Azure infrastructure
- **Scalable:** Can easily handle 50 concurrent users with room for growth
- **Secure:** Industry-standard encryption and security protocols

**Capacity Planning:**
- System designed for 50+ concurrent users
- Database optimized with 40+ performance indexes
- Can scale up if user base grows beyond 50

---

## Technical Highlights (Simple Explanation)

- **Automatic Data Sync:** Connects to RADAR system to get voyage and claim updates automatically
- **Real-Time Updates:** Changes appear instantly for all users
- **Mobile-Friendly:** Works on tablets and phones, not just desktop computers
- **Dark Mode:** Easy on the eyes for long working hours
- **Cloud Storage:** Documents stored securely in the cloud, accessible from anywhere
- **Background Processing:** Heavy calculations happen in the background so your screen doesn't freeze

---

## Data You Can Track

### **Claims Data:**
- Claim status, amounts, and payment tracking
- Demurrage calculations and rates
- Time-barred status and deadlines
- Comments and discussion history
- Attached documents and files

### **Voyage Data:**
- Vessel details and voyage numbers
- Loading and discharge ports
- Contract terms and laytime
- RADAR synchronization status
- Assignment history

### **Fleet Data:**
- Vessel specifications and technical details
- Time charter contracts and rates
- Charter expiry dates with visual alerts
- Ship owner and charterer information

### **Port Activities:**
- Activity types (loading, discharging, dry-docking, etc.)
- Estimated vs. actual dates
- Duration tracking (days and hours)
- Activity history for each vessel

---

## User Experience Improvements

### **Before (Qlik Sense/Vizlib):**
1. Open Qlik Sense app (wait for loading)
2. Navigate to writeback table (wait for rendering)
3. Find your row among hundreds (scroll, scroll, scroll)
4. Click to edit (wait for edit mode)
5. Make one change (click save)
6. Wait for save to complete (freezing...)
7. Repeat for each field you need to update
8. No way to add comments or documents
9. No history of who changed what
10. Hope no one else is editing the same row

### **After (New System):**
1. Log in to personal dashboard (instant load)
2. See your assigned voyages on the front page
3. Click on a claim (instant load)
4. Edit multiple fields at once
5. Add comments for your team
6. Attach documents if needed
7. Save everything in one click (instant save)
8. See complete history of changes
9. System prevents conflicts if someone else is editing
10. Get visual alerts for urgent items

---

## Return on Investment

### **Time Savings:**
- **Reduced clicking:** Estimate 50-70% less clicking per claim
- **Faster data entry:** Automatic RADAR sync eliminates manual entry
- **Quick searching:** Find claims in seconds instead of minutes
- **Instant exports:** Generate reports in seconds, not hours

### **Quality Improvements:**
- **Fewer errors:** Automatic calculations and validation
- **Better tracking:** Nothing falls through the cracks
- **Improved collaboration:** Team discussions documented in system
- **Audit compliance:** Complete history for regulatory requirements

### **Business Benefits:**
- **No more system crashes:** Reliable performance during peak times
- **Scalable solution:** Can grow with your business
- **Better insights:** Analytics dashboard for data-driven decisions
- **Professional image:** Modern system for stakeholder presentations

---

## Security & Compliance

- **Secure login:** Each user has their own credentials
- **Role-based access:** Users only see what they should see
- **Activity logging:** Every action is tracked for audit purposes
- **Data encryption:** Information protected during transmission
- **Session management:** Automatic logout after period of inactivity
- **File upload security:** Only approved file types allowed
- **Rate limiting:** Protection against system abuse

---

## Support & Training

- **User-friendly interface:** Intuitive design requires minimal training
- **Role-based training:** Each role gets training specific to their needs
- **Documentation:** Step-by-step guides for all features
- **Personal dashboard:** Quick start guide built into the system
- **Help resources:** Available within the application

---

## Next Steps

1. **Review this summary** with key stakeholders
2. **Schedule demo session** to see the system in action
3. **Identify pilot users** for initial testing (5-10 users from Krakow and London)
4. **Plan migration** from Qlik Sense to new system
5. **Schedule training sessions** for each role level
6. **Deploy to Azure VM** in Europe region
7. **Go live** with full team (50 users)

---

## Questions & Answers

### **Q: Will this work with our existing RADAR system?**
**A:** Yes, the system is built to automatically sync data from RADAR, so you won't need to enter data twice.

### **Q: What happens if two people edit the same claim?**
**A:** The system has built-in conflict prevention. The second person will be notified and can review changes before saving.

### **Q: Can we access this from home or while traveling?**
**A:** Yes, it's a web-based system accessible from anywhere with an internet connection and proper login credentials.

### **Q: How long will the migration take?**
**A:** Migration timeline depends on data volume, but typically 2-4 weeks including testing and training.

### **Q: What if we need to add more users in the future?**
**A:** The system is designed to scale. Adding more users is straightforward and doesn't require major changes.

### **Q: Will we lose our historical data from Qlik Sense?**
**A:** No, historical data can be migrated to the new system during the implementation phase.

### **Q: What happens if the system goes down?**
**A:** Azure infrastructure provides 99.9% uptime. In the rare event of downtime, automatic backups ensure no data loss.

### **Q: How much will hosting cost per month?**
**A:** Azure VM hosting for 50 users typically costs €150-300/month depending on configuration (subject to Azure pricing).

---

## Contact Information

For questions about this project or to schedule a demonstration:
- **Project Documentation:** See [docs/](./docs/) folder for detailed technical information
- **Testing Information:** See [docs/project/WHAT_ARE_TESTS.md](./docs/project/WHAT_ARE_TESTS.md)
- **Setup Guide:** See [docs/guides/BUSINESS_LAPTOP_SETUP.md](./docs/guides/BUSINESS_LAPTOP_SETUP.md) for stakeholder presentation setup

---

**Document Version:** 1.0
**Last Updated:** January 2026
**Target Audience:** Non-technical stakeholders, management, business users
