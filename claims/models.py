from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class User(AbstractUser):
    """Extended User model with role-based permissions"""

    ROLE_CHOICES = [
        ('READ', 'Read Only'),
        ('READ_EXPORT', 'Read + Export'),
        ('WRITE', 'Write'),
        ('TEAM_LEAD', 'Team Lead'),
        ('ADMIN', 'Administrator'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='READ')
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="Job title/position")
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    dark_mode = models.BooleanField(default=False, help_text="Enable dark mode preference")
    must_change_password = models.BooleanField(default=True, help_text="User must change password on first login")
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='users_created')
    bio = models.TextField(blank=True, help_text="Short biography")

    def can_export(self) -> bool:
        return self.role in ['READ_EXPORT', 'WRITE', 'TEAM_LEAD', 'ADMIN']

    def can_write(self) -> bool:
        return self.role in ['WRITE', 'TEAM_LEAD', 'ADMIN']

    def is_admin_role(self) -> bool:
        return self.role == 'ADMIN'

    def is_team_lead(self) -> bool:
        """Check if user has team lead or admin role"""
        return self.role in ['TEAM_LEAD', 'ADMIN']

    def can_assign_voyages(self) -> bool:
        """Check if user can assign voyages to others"""
        return self.role in ['TEAM_LEAD', 'ADMIN']

    def get_assigned_voyages_count(self) -> int:
        """Count of voyages assigned to this user"""
        return self.assigned_voyages.count()

    def get_closed_claims_count(self) -> int:
        """Count of claims that are paid (closed/recovered)"""
        return self.assigned_claims.filter(payment_status='PAID').count()

    class Meta:
        db_table = 'claims_user'
        permissions = [
            ('view_user_directory', 'Can view user directory'),
            ('export_users', 'Can export users to Excel'),
        ]


class ShipOwner(models.Model):
    """Ship Owner / Charterer information"""

    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True, help_text="Owner code from RADAR")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),  # For search and lookups
            models.Index(fields=['code']),  # For RADAR sync lookups
            models.Index(fields=['is_active']),  # Filter active owners
            models.Index(fields=['is_active', 'name']),  # Active owners list
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Voyage(models.Model):
    """Voyage from RADAR system - central entity for claims management"""

    ASSIGNMENT_STATUS_CHOICES = [
        ('UNASSIGNED', 'Unassigned'),
        ('ASSIGNED', 'Assigned'),
        ('COMPLETED', 'Completed'),
    ]

    CHARTER_TYPE_CHOICES = [
        ('SPOT', 'Spot - 3rd Party Ship'),
        ('TRADED', 'Traded - Time Charter Ship'),
    ]

    # RADAR system fields
    radar_voyage_id = models.CharField(max_length=100, unique=True, help_text="Unique ID from RADAR")
    voyage_number = models.CharField(max_length=100)
    vessel_name = models.CharField(max_length=200)
    imo_number = models.CharField(max_length=20, blank=True)
    charter_type = models.CharField(
        max_length=10,
        choices=CHARTER_TYPE_CHOICES,
        default='SPOT',
        help_text="SPOT = 3rd party ship, TRADED = Time Charter ship"
    )

    # Voyage details
    charter_party = models.CharField(max_length=100)
    load_port = models.CharField(max_length=100)
    discharge_port = models.CharField(max_length=100)
    laycan_start = models.DateField(help_text="Laycan start date")
    laycan_end = models.DateField(help_text="Laycan end date")

    # Business relationships
    ship_owner = models.ForeignKey(ShipOwner, on_delete=models.PROTECT, related_name='voyages')

    # Contract terms
    demurrage_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Demurrage rate per day"
    )
    laytime_allowed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Allowed laytime in days"
    )
    currency = models.CharField(max_length=3, default='USD')

    # Assignment
    assignment_status = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_STATUS_CHOICES,
        default='UNASSIGNED'
    )
    assigned_analyst = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_voyages',
        limit_choices_to={'role__in': ['WRITE', 'ADMIN']}
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    # RADAR sync tracking
    last_radar_sync = models.DateTimeField(auto_now=True)
    radar_data = models.JSONField(default=dict, blank=True, help_text="Raw data from RADAR")

    # Concurrency Control (Optimistic Locking)
    version = models.IntegerField(default=0, help_text="Version number for optimistic locking")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Single-column indexes for lookups
            models.Index(fields=['radar_voyage_id']),
            models.Index(fields=['assignment_status']),
            models.Index(fields=['assigned_analyst']),
            models.Index(fields=['ship_owner']),
            models.Index(fields=['voyage_number']),  # For search and lookups
            models.Index(fields=['vessel_name']),  # For search
            models.Index(fields=['created_at']),  # For ordering and date filtering
            models.Index(fields=['laycan_start']),  # For date range queries

            # Composite indexes for common query patterns (SQL Server optimized)
            models.Index(fields=['ship_owner', 'assignment_status']),  # Owner voyage list
            models.Index(fields=['assigned_analyst', 'assignment_status']),  # Analyst workload
            models.Index(fields=['assignment_status', 'created_at']),  # Unassigned voyages report
        ]

    def __str__(self) -> str:
        return f"{self.voyage_number} - {self.vessel_name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Optimistic Locking: Check for concurrent modifications
        if self.pk is not None:  # Only check for existing records
            # Get the current version from database
            current = Voyage.objects.filter(pk=self.pk).values('version').first()
            if current and current['version'] != self.version:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    "This voyage has been modified by another user. "
                    "Please reload the page and try again."
                )
            # Increment version for next save
            self.version += 1

        super().save(*args, **kwargs)

    def assign_to(self, analyst: User, assigned_by: Optional[User] = None) -> None:
        """Assign voyage to analyst and create assignment history record"""
        # Store old assignment for history
        old_analyst = self.assigned_analyst

        # Update voyage assignment
        self.assigned_analyst = analyst
        self.assignment_status = 'ASSIGNED'
        self.assigned_at = timezone.now()
        self.save()

        # Close previous active assignment if exists
        if old_analyst:
            VoyageAssignment.objects.filter(
                voyage=self,
                is_active=True
            ).update(
                is_active=False,
                unassigned_at=timezone.now()
            )

        # Create new assignment history record
        VoyageAssignment.objects.create(
            voyage=self,
            assigned_to=analyst,
            assigned_by=assigned_by or analyst,  # If not specified, assume self-assignment
            is_active=True
        )

        # Update all existing claims for this voyage
        self.claims.filter(assigned_to__isnull=True).update(assigned_to=analyst)


class VoyageAssignment(models.Model):
    """Assignment history tracking for voyages - provides audit trail and reporting"""

    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, related_name='assignment_history')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='voyage_assignments',
        help_text="Analyst assigned to this voyage"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='voyage_assignments_made',
        help_text="Team lead or user who made the assignment"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True, help_text="When this assignment ended")
    is_active = models.BooleanField(default=True, help_text="Current active assignment")
    reassignment_reason = models.TextField(blank=True, help_text="Reason for reassignment (if applicable)")

    class Meta:
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['voyage', 'is_active']),
            models.Index(fields=['assigned_to', 'is_active']),
            models.Index(fields=['assigned_at']),
        ]

    def __str__(self) -> str:
        status = "Active" if self.is_active else "Completed"
        return f"{self.voyage.voyage_number} → {self.assigned_to.get_full_name()} ({status})"

    @property
    def duration(self) -> timedelta:
        """Calculate duration of assignment"""
        if self.unassigned_at:
            return self.unassigned_at - self.assigned_at
        return timezone.now() - self.assigned_at

    @property
    def duration_days(self) -> int:
        """Get duration in days"""
        return self.duration.days


class Claim(models.Model):
    """Main Claims model for demurrage and post-deal claims"""

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('UNDER_REVIEW', 'Under Review'),
        ('SUBMITTED', 'Submitted'),
        ('SETTLED', 'Settled'),
        ('REJECTED', 'Rejected'),
    ]

    CLAIM_TYPE_CHOICES = [
        ('DEMURRAGE', 'Demurrage'),
        ('POST_DEAL', 'Post-Deal'),
        ('DESPATCH', 'Despatch'),
        ('DEAD_FREIGHT', 'Dead Freight'),
        ('OTHER', 'Other'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('NOT_SENT', 'Not Sent'),
        ('SENT', 'Sent to Owner'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('TIMEBAR', 'Time-barred'),
        ('DISPUTED', 'Disputed'),
    ]

    COST_TYPE_CHOICES = [
        ('PORT_COSTS', 'Port Costs'),
        ('CANAL_COSTS', 'Canal Costs'),
        ('BUNKER_COSTS', 'Bunker Costs'),
        ('AGENCY_FEES', 'Agency Fees'),
        ('DEMURRAGE', 'Demurrage'),
        ('DESPATCH', 'Despatch'),
        ('OTHER', 'Other'),
    ]

    # Basic Information
    claim_number = models.CharField(max_length=50, unique=True, editable=False)
    radar_claim_id = models.CharField(max_length=100, unique=True, null=True, blank=True, help_text="Unique ID from RADAR")
    claim_type = models.CharField(max_length=20, choices=CLAIM_TYPE_CHOICES)
    cost_type = models.CharField(max_length=50, choices=COST_TYPE_CHOICES, blank=True, help_text="Specific cost type for post-deal claims")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='NOT_SENT')

    # Voyage Relationship (central link)
    voyage = models.ForeignKey(Voyage, on_delete=models.PROTECT, related_name='claims')
    ship_owner = models.ForeignKey(ShipOwner, on_delete=models.PROTECT, related_name='claims')

    # Claim Details
    laytime_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual laytime used in days (for demurrage claims)"
    )
    demurrage_days = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Calculated demurrage days"
    )
    claim_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total claim amount"
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Amount already paid by owner"
    )
    currency = models.CharField(max_length=3, default='USD')

    # Timebar and Deadlines
    claim_deadline = models.DateField(null=True, blank=True, help_text="Contractual deadline to submit claim")
    is_time_barred = models.BooleanField(default=False, help_text="Claim missed contractual deadline")
    time_bar_date = models.DateField(null=True, blank=True, help_text="Date when claim became time-barred")

    # Description and Notes
    description = models.TextField(blank=True)
    settlement_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes from RADAR or analysts")

    # Ownership and Tracking
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_claims')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_claims')

    # RADAR tracking
    last_radar_sync = models.DateTimeField(null=True, blank=True)
    radar_data = models.JSONField(default=dict, blank=True)

    # Concurrency Control (Optimistic Locking)
    version = models.IntegerField(default=0, help_text="Version number for optimistic locking")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    sent_to_owner_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Single-column indexes for lookups
            models.Index(fields=['claim_number']),
            models.Index(fields=['radar_claim_id']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['voyage']),
            models.Index(fields=['ship_owner']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['is_time_barred']),
            models.Index(fields=['created_at']),  # For ordering and date filtering
            models.Index(fields=['created_by']),  # For user's claims queries
            models.Index(fields=['claim_deadline']),  # For deadline alerts

            # Composite indexes for common query patterns (SQL Server optimized)
            models.Index(fields=['assigned_to', 'status']),  # Analyst dashboard
            models.Index(fields=['ship_owner', 'payment_status']),  # Analytics by owner
            models.Index(fields=['status', 'created_at']),  # Status reports with date
            models.Index(fields=['is_time_barred', 'payment_status']),  # Time-barred reports
            models.Index(fields=['voyage', 'status']),  # Voyage claim summary
        ]

    def __str__(self) -> str:
        return f"{self.claim_number} - {self.voyage.vessel_name} ({self.get_claim_type_display()})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Optimistic Locking: Check for concurrent modifications
        if self.pk is not None:  # Only check for existing records
            # Get the current version from database
            current = Claim.objects.filter(pk=self.pk).values('version').first()
            if current and current['version'] != self.version:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    "This claim has been modified by another user. "
                    "Please reload the page and try again."
                )
            # Increment version for next save
            self.version += 1

        if not self.claim_number:
            # Generate claim number
            timestamp = timezone.now().strftime('%Y%m%d')
            last_claim = Claim.objects.filter(claim_number__startswith=f'CLM-{timestamp}').order_by('-claim_number').first()
            if last_claim:
                last_seq = int(last_claim.claim_number.split('-')[-1])
                new_seq = last_seq + 1
            else:
                new_seq = 1
            self.claim_number = f'CLM-{timestamp}-{new_seq:04d}'

        # Calculate demurrage days if applicable
        if self.claim_type == 'DEMURRAGE' and self.laytime_used and self.voyage:
            self.demurrage_days = max(Decimal('0'), self.laytime_used - self.voyage.laytime_allowed)

        # Auto-assign from voyage if not assigned
        if not self.assigned_to and self.voyage and self.voyage.assigned_analyst:
            self.assigned_to = self.voyage.assigned_analyst

        # Check and update timebar status
        if self.claim_deadline and not self.is_time_barred:
            if timezone.now().date() > self.claim_deadline and self.payment_status == 'NOT_SENT':
                self.is_time_barred = True
                self.time_bar_date = timezone.now().date()
                self.payment_status = 'TIMEBAR'

        super().save(*args, **kwargs)

    @property
    def outstanding_amount(self) -> Decimal:
        """Calculate outstanding amount"""
        return self.claim_amount - self.paid_amount

    @property
    def vessel_name(self) -> str:
        """Get vessel name from voyage"""
        return self.voyage.vessel_name if self.voyage else "N/A"

    @property
    def voyage_number(self) -> str:
        """Get voyage number from voyage"""
        return self.voyage.voyage_number if self.voyage else "N/A"

    def can_edit(self, user: User) -> bool:
        """Check if user can edit this claim"""
        if user.is_admin_role():
            return True
        if self.status == 'DRAFT' and (self.created_by == user or self.assigned_to == user):
            return user.can_write()
        return False

    def can_delete(self, user: User) -> bool:
        """Check if user can delete this claim"""
        return user.is_admin_role() or (self.status == 'DRAFT' and self.created_by == user and user.can_write())


class ClaimActivityLog(models.Model):
    """Activity log for critical claim operations - targeted audit trail"""

    ACTION_CHOICES = [
        ('CREATED', 'Claim Created'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('PAYMENT_STATUS_CHANGED', 'Payment Status Changed'),
        ('AMOUNT_CHANGED', 'Claim Amount Changed'),
        ('PAID_AMOUNT_CHANGED', 'Paid Amount Changed'),
        ('ASSIGNED', 'Claim Assigned'),
        ('REASSIGNED', 'Claim Reassigned'),
        ('DEADLINE_CHANGED', 'Deadline Changed'),
        ('TIME_BARRED', 'Marked Time-Barred'),
        ('DELETED', 'Claim Deleted'),
    ]

    claim = models.ForeignKey(
        Claim,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
        help_text="The claim this activity is associated with"
    )
    claim_number = models.CharField(max_length=50, help_text="Claim number for reference (in case claim is deleted)")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who performed the action"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    message = models.TextField(help_text="Description of what changed")
    old_value = models.TextField(blank=True, help_text="Previous value (if applicable)")
    new_value = models.TextField(blank=True, help_text="New value (if applicable)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['claim', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self) -> str:
        claim_ref = self.claim.claim_number if self.claim else self.claim_number
        return f"{claim_ref} - {self.get_action_display()} by {self.user.username if self.user else 'System'}"

    @property
    def action_icon(self) -> str:
        """Get Bootstrap icon for action type"""
        icons = {
            'CREATED': 'plus-circle',
            'STATUS_CHANGED': 'arrow-right-circle',
            'PAYMENT_STATUS_CHANGED': 'cash-coin',
            'AMOUNT_CHANGED': 'currency-dollar',
            'PAID_AMOUNT_CHANGED': 'credit-card',
            'ASSIGNED': 'person-check',
            'REASSIGNED': 'arrow-left-right',
            'DEADLINE_CHANGED': 'calendar-event',
            'TIME_BARRED': 'exclamation-triangle',
            'DELETED': 'trash',
        }
        return icons.get(self.action, 'circle')

    @property
    def action_color(self) -> str:
        """Get Bootstrap color class for action type"""
        colors = {
            'CREATED': 'success',
            'STATUS_CHANGED': 'info',
            'PAYMENT_STATUS_CHANGED': 'primary',
            'AMOUNT_CHANGED': 'warning',
            'PAID_AMOUNT_CHANGED': 'success',
            'ASSIGNED': 'info',
            'REASSIGNED': 'warning',
            'DEADLINE_CHANGED': 'warning',
            'TIME_BARRED': 'danger',
            'DELETED': 'danger',
        }
        return colors.get(self.action, 'secondary')


class Comment(models.Model):
    """Comments on claims for discussion and tracking"""

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['claim', 'created_at']),  # Comments for a claim
            models.Index(fields=['user']),  # Comments by user
        ]

    def __str__(self) -> str:
        return f"Comment on {self.claim.claim_number} by {self.user.username}"


def claim_document_path(instance: 'Document', filename: str) -> str:
    """
    Generate hierarchical path for document uploads.
    Path structure: voyages/{voyage_id}/claims/{claim_id}/documents/{filename}
    This structure supports both local filesystem and cloud storage (Azure Blob, SharePoint).
    """
    voyage_id = instance.claim.voyage.id
    claim_id = instance.claim.id
    return f'voyages/{voyage_id}/claims/{claim_id}/documents/{filename}'


class Document(models.Model):
    """Document attachments for claims"""

    DOCUMENT_TYPE_CHOICES = [
        ('CHARTER_PARTY', 'Charter Party'),
        ('SOF', 'Statement of Facts'),
        ('LAYTIME_CALC', 'Laytime Calculation'),
        ('CORRESPONDENCE', 'Correspondence'),
        ('INVOICE', 'Invoice'),
        ('OTHER', 'Other'),
    ]

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to=claim_document_path)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['claim', 'uploaded_at']),  # Documents for a claim
            models.Index(fields=['document_type']),  # Filter by document type
            models.Index(fields=['uploaded_by']),  # Documents by user
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.claim.claim_number}"

    @property
    def filename(self) -> str:
        return self.file.name.split('/')[-1]
