from django.db import models
from django.utils import timezone


class Ship(models.Model):
    """
    Ship master data with technical specifications.
    Supports both SPOT voyages and Time Charter (TC) fleet management.
    """

    VESSEL_TYPE_CHOICES = [
        ('VLCC', 'Very Large Crude Carrier (VLCC)'),
        ('SUEZMAX', 'Suezmax Tanker'),
        ('AFRAMAX', 'Aframax Tanker'),
        ('PANAMAX', 'Panamax Tanker'),
        ('MR', 'Medium Range Tanker'),
        ('LR1', 'Long Range 1 Tanker'),
        ('LR2', 'Long Range 2 Tanker'),
        ('HANDYSIZE', 'Handysize Tanker'),
        ('OTHER', 'Other'),
    ]

    CHARTER_TYPE_CHOICES = [
        ('SPOT', 'Spot Charter'),
        ('TIME_CHARTER', 'Time Charter'),
        ('BAREBOAT', 'Bareboat Charter'),
    ]

    # Identification
    imo_number = models.CharField(
        max_length=10,
        unique=True,
        help_text="IMO number (unique identifier)"
    )
    vessel_name = models.CharField(max_length=200, db_index=True)

    # Technical Specifications
    vessel_type = models.CharField(max_length=20, choices=VESSEL_TYPE_CHOICES)
    built_year = models.IntegerField(help_text="Year vessel was built")
    flag = models.CharField(max_length=50, blank=True)
    deadweight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Deadweight tonnage (DWT)"
    )
    gross_tonnage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Gross tonnage (GT)"
    )

    # Engine & Capacity
    engine_type = models.CharField(max_length=100, blank=True)
    engine_power = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Engine power in kW"
    )
    cargo_capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cargo capacity in cubic meters"
    )

    # Charter Information
    charter_type = models.CharField(
        max_length=20,
        choices=CHARTER_TYPE_CHOICES,
        default='SPOT',
        help_text="Type of charter"
    )
    is_tc_fleet = models.BooleanField(
        default=False,
        help_text="Is this vessel part of Time Charter fleet?"
    )
    charter_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date of time charter (if applicable)"
    )
    charter_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date of time charter (if applicable)"
    )
    daily_hire_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Daily hire rate in USD (for TC fleet)"
    )
    tc_charterer = models.CharField(
        max_length=200,
        blank=True,
        help_text="Charterer name (for TC fleet)"
    )

    # Status & Additional Info
    is_active = models.BooleanField(default=True, help_text="Is vessel currently active?")
    notes = models.TextField(blank=True)

    # Sync Info (for external database integration)
    external_db_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID from external TC fleet database"
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last sync from external database"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['vessel_name']
        indexes = [
            models.Index(fields=['imo_number']),
            models.Index(fields=['vessel_name']),
            models.Index(fields=['vessel_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_tc_fleet']),
            models.Index(fields=['charter_type']),
            models.Index(fields=['is_tc_fleet', 'charter_end_date']),  # TC fleet management
            models.Index(fields=['is_active', 'vessel_name']),  # Active vessels list
        ]

    def __str__(self):
        return f"{self.vessel_name} (IMO: {self.imo_number})"

    def get_voyage_history(self):
        """Get all voyages for this ship (from claims app)"""
        from claims.models import Voyage
        return Voyage.objects.filter(
            imo_number=self.imo_number
        ).select_related('ship_owner', 'assigned_analyst').order_by('-laycan_start')

    def get_claim_history(self):
        """Get all claims for this ship's voyages (from claims app)"""
        from claims.models import Claim
        return Claim.objects.filter(
            voyage__imo_number=self.imo_number
        ).select_related('voyage', 'ship_owner', 'assigned_to').order_by('-created_at')

    @property
    def is_charter_active(self):
        """Check if time charter is currently active"""
        if not self.is_tc_fleet or not self.charter_start_date or not self.charter_end_date:
            return False
        today = timezone.now().date()
        return self.charter_start_date <= today <= self.charter_end_date

    @property
    def charter_days_remaining(self):
        """Calculate days remaining in time charter"""
        if not self.is_charter_active or not self.charter_end_date:
            return 0
        today = timezone.now().date()
        return (self.charter_end_date - today).days
