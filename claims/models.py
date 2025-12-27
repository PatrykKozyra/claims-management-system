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
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="Job title/position")
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    dark_mode = models.BooleanField(default=False, help_text="Enable dark mode preference")
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='users_created')
    bio = models.TextField(blank=True, help_text="Short biography")

    def can_export(self):
        return self.role in ['READ_EXPORT', 'WRITE', 'TEAM_LEAD', 'ADMIN']

    def can_write(self):
        return self.role in ['WRITE', 'TEAM_LEAD', 'ADMIN']

    def is_admin_role(self):
        return self.role == 'ADMIN'

    def is_team_lead(self):
        """Check if user has team lead or admin role"""
        return self.role in ['TEAM_LEAD', 'ADMIN']

    def can_assign_voyages(self):
        """Check if user can assign voyages to others"""
        return self.role in ['TEAM_LEAD', 'ADMIN']

    def get_assigned_voyages_count(self):
        """Count of voyages assigned to this user"""
        return self.assigned_voyages.count()

    def get_closed_claims_count(self):
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

    def __str__(self):
        return f"{self.name} ({self.code})"


class Voyage(models.Model):
    """Voyage from RADAR system - central entity for claims management"""

    ASSIGNMENT_STATUS_CHOICES = [
        ('UNASSIGNED', 'Unassigned'),
        ('ASSIGNED', 'Assigned'),
        ('COMPLETED', 'Completed'),
    ]

    # RADAR system fields
    radar_voyage_id = models.CharField(max_length=100, unique=True, help_text="Unique ID from RADAR")
    voyage_number = models.CharField(max_length=100)
    vessel_name = models.CharField(max_length=200)
    imo_number = models.CharField(max_length=20, blank=True)

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

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['radar_voyage_id']),
            models.Index(fields=['assignment_status']),
            models.Index(fields=['assigned_analyst']),
        ]

    def __str__(self):
        return f"{self.voyage_number} - {self.vessel_name}"

    def assign_to(self, analyst):
        """Assign voyage to analyst"""
        self.assigned_analyst = analyst
        self.assignment_status = 'ASSIGNED'
        self.assigned_at = timezone.now()
        self.save()

        # Update all existing claims for this voyage
        self.claims.filter(assigned_to__isnull=True).update(assigned_to=analyst)


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
            models.Index(fields=['claim_number']),
            models.Index(fields=['radar_claim_id']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['voyage']),
            models.Index(fields=['ship_owner']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['is_time_barred']),
        ]

    def __str__(self):
        return f"{self.claim_number} - {self.voyage.vessel_name} ({self.get_claim_type_display()})"

    def save(self, *args, **kwargs):
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
    def outstanding_amount(self):
        """Calculate outstanding amount"""
        return self.claim_amount - self.paid_amount

    @property
    def vessel_name(self):
        """Get vessel name from voyage"""
        return self.voyage.vessel_name if self.voyage else "N/A"

    @property
    def voyage_number(self):
        """Get voyage number from voyage"""
        return self.voyage.voyage_number if self.voyage else "N/A"

    def can_edit(self, user):
        """Check if user can edit this claim"""
        if user.is_admin_role():
            return True
        if self.status == 'DRAFT' and (self.created_by == user or self.assigned_to == user):
            return user.can_write()
        return False

    def can_delete(self, user):
        """Check if user can delete this claim"""
        return user.is_admin_role() or (self.status == 'DRAFT' and self.created_by == user and user.can_write())


class Comment(models.Model):
    """Comments on claims for discussion and tracking"""

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.claim.claim_number} by {self.user.username}"


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
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.claim.claim_number}"

    @property
    def filename(self):
        return self.file.name.split('/')[-1]
