from __future__ import annotations
from typing import Any

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class ActivityType(models.Model):
    """Types of port activities"""

    CATEGORY_CHOICES = [
        ('CARGO_OPS', 'Cargo Operations'),
        ('BALLASTING', 'Ballasting Operations'),
        ('CLEANING', 'Cleaning & Preparation'),
        ('BUNKERING', 'Bunkering & Supplies'),
        ('MAINTENANCE', 'Maintenance & Repairs'),
        ('OPERATIONAL', 'Operational Status'),
        ('ADMINISTRATIVE', 'Administrative & Compliance'),
        ('OFFHIRE', 'Off-hire Events'),
        ('TRANSIT', 'Transit & Navigation'),
        ('COMMERCIAL', 'Commercial Activities'),
    ]

    # Activity codes matching your specifications
    code = models.CharField(
        max_length=50,
        unique=True,
        default='general',
        help_text="Activity code (e.g., load, discharge, bunkering)"
    )
    name = models.CharField(max_length=100, help_text="Display name")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    icon_class = models.CharField(
        max_length=50,
        blank=True,
        help_text="Bootstrap icon class for UI display"
    )
    color_class = models.CharField(
        max_length=50,
        blank=True,
        help_text="CSS color class for UI display"
    )

    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_category_display()})"


class PortActivity(models.Model):
    """
    Timeline of port activities for ships.
    Supports estimated vs. actual dates from RADAR system.
    """

    DATE_STATUS_CHOICES = [
        ('ESTIMATED', 'Estimated'),
        ('ACTUAL', 'Actual'),
    ]

    # Link to Ship (from ships app) and Voyage (from claims app)
    ship = models.ForeignKey(
        'ships.Ship',
        on_delete=models.PROTECT,
        related_name='port_activities',
        help_text="Ship performing this activity"
    )
    voyage = models.ForeignKey(
        'claims.Voyage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='port_activities',
        help_text="Related voyage (if applicable)"
    )

    # Activity Details
    activity_type = models.ForeignKey(ActivityType, on_delete=models.PROTECT)

    # Port Information
    load_port = models.CharField(
        max_length=200,
        blank=True,
        help_text="Loading port name (for loading/discharging activities)"
    )
    discharge_port = models.CharField(
        max_length=200,
        blank=True,
        help_text="Discharge port name (for loading/discharging activities)"
    )
    port_name = models.CharField(
        max_length=200,
        help_text="Port where activity takes place"
    )

    # Timeline with Estimated vs Actual tracking
    start_datetime = models.DateTimeField(help_text="Activity start date/time")
    start_date_status = models.CharField(
        max_length=10,
        choices=DATE_STATUS_CHOICES,
        default='ESTIMATED',
        help_text="Is start date estimated or actual?"
    )

    end_datetime = models.DateTimeField(help_text="Activity end date/time")
    end_date_status = models.CharField(
        max_length=10,
        choices=DATE_STATUS_CHOICES,
        default='ESTIMATED',
        help_text="Is end date estimated or actual?"
    )

    duration = models.DurationField(
        editable=False,
        help_text="Auto-calculated duration (end - start)"
    )

    # Additional Info
    cargo_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cargo quantity (tons)"
    )
    notes = models.TextField(
        blank=True,
        help_text="System notes from RADAR (read-only)"
    )

    # User Comments (only editable field)
    user_comments = models.TextField(
        blank=True,
        help_text="User comments - only editable field"
    )

    # RADAR sync tracking
    radar_activity_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Activity ID from RADAR system"
    )
    last_radar_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last sync from RADAR"
    )

    # Audit
    created_by = models.ForeignKey(
        'claims.User',
        on_delete=models.PROTECT,
        related_name='activities_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ship', 'start_datetime']
        verbose_name_plural = 'Port Activities'
        indexes = [
            # Single-column indexes
            models.Index(fields=['ship', 'start_datetime']),  # Ship timeline
            models.Index(fields=['voyage']),  # Voyage activities
            models.Index(fields=['activity_type']),  # Filter by activity type
            models.Index(fields=['start_datetime']),  # Date filtering
            models.Index(fields=['start_date_status']),  # Estimated vs actual
            models.Index(fields=['end_date_status']),

            # Composite indexes for filtering
            models.Index(fields=['ship', 'activity_type', 'start_datetime']),  # Ship + type
            models.Index(fields=['voyage', 'start_datetime']),  # Voyage timeline
            models.Index(fields=['activity_type', 'start_datetime']),  # Activity reports
        ]

    def __str__(self) -> str:
        return f"{self.ship.vessel_name} - {self.activity_type.name} at {self.port_name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Auto-calculate duration
        if self.start_datetime and self.end_datetime:
            self.duration = self.end_datetime - self.start_datetime

        # Validate dates
        if self.end_datetime <= self.start_datetime:
            raise ValidationError("End datetime must be after start datetime")

        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate no overlapping activities for same ship"""
        if self.start_datetime and self.end_datetime:
            # Check for overlapping activities on same ship
            overlapping = PortActivity.objects.filter(
                ship=self.ship,
                start_datetime__lt=self.end_datetime,
                end_datetime__gt=self.start_datetime
            ).exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError(
                    f"Activity overlaps with existing activity: {overlapping.first()}"
                )

    @property
    def duration_hours(self) -> float:
        """Get duration in hours"""
        return self.duration.total_seconds() / 3600 if self.duration else 0

    @property
    def duration_days(self) -> int:
        """Get duration in days"""
        return self.duration.days if self.duration else 0

    @property
    def is_fully_actual(self) -> bool:
        """Check if both start and end dates are actual"""
        return (self.start_date_status == 'ACTUAL' and
                self.end_date_status == 'ACTUAL')

    @property
    def is_fully_estimated(self) -> bool:
        """Check if both start and end dates are estimated"""
        return (self.start_date_status == 'ESTIMATED' and
                self.end_date_status == 'ESTIMATED')

    @property
    def date_status_display(self) -> str:
        """Get friendly display of date status"""
        if self.is_fully_actual:
            return "Actual"
        elif self.is_fully_estimated:
            return "Estimated"
        else:
            return f"Start: {self.get_start_date_status_display()}, End: {self.get_end_date_status_display()}"
