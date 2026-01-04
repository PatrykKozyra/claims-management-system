from __future__ import annotations
from typing import Optional, Any
from django.db.models import QuerySet

from django.db import models
from django.utils import timezone
from decimal import Decimal


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

    def __str__(self) -> str:
        return f"{self.vessel_name} (IMO: {self.imo_number})"

    def get_voyage_history(self) -> QuerySet:
        """Get all voyages for this ship (from claims app)"""
        from claims.models import Voyage
        return Voyage.objects.filter(
            imo_number=self.imo_number
        ).select_related('ship_owner', 'assigned_analyst').order_by('-laycan_start')

    def get_claim_history(self) -> QuerySet:
        """Get all claims for this ship's voyages (from claims app)"""
        from claims.models import Claim
        return Claim.objects.filter(
            voyage__imo_number=self.imo_number
        ).select_related('voyage', 'ship_owner', 'assigned_to').order_by('-created_at')

    @property
    def is_charter_active(self) -> bool:
        """Check if time charter is currently active"""
        if not self.is_tc_fleet or not self.charter_start_date or not self.charter_end_date:
            return False
        today = timezone.now().date()
        return self.charter_start_date <= today <= self.charter_end_date

    @property
    def charter_days_remaining(self) -> int:
        """Calculate days remaining in time charter"""
        if not self.is_charter_active or not self.charter_end_date:
            return 0
        today = timezone.now().date()
        return (self.charter_end_date - today).days


class TCFleet(models.Model):
    """
    Time Charter Fleet - Individual TC contracts.
    Each record represents one time charter contract.
    Same ship (IMO) can have multiple contracts over time.
    """

    SHIP_TYPE_CHOICES = [
        ('AFRAMAX', 'Aframax'),
        ('SUEZMAX', 'Suezmax'),
        ('VLCC', 'VLCC'),
        ('PANAMAX', 'Panamax'),
        ('MR', 'Mid Range'),
        ('LR1', 'Long Range 1'),
        ('LR2', 'Long Range 2'),
        ('HANDYSIZE', 'Handysize'),
        ('CHEMICAL', 'Chemical Tanker'),
        ('PRODUCT', 'Product Tanker'),
        ('OTHER', 'Other'),
    ]

    DELIVERY_STATUS_CHOICES = [
        ('INCOMING_TC', 'Incoming TC'),
        ('ON_TC', 'On TC'),
        ('REDELIVERED', 'Redelivered'),
    ]

    TRADE_CHOICES = [
        ('CRUDE', 'Crude'),
        ('PRODUCTS', 'Products'),
        ('CHEMICAL', 'Chemical'),
        ('MIXED', 'Mixed'),
    ]

    BUNKERS_POLICY_CHOICES = [
        ('CHARTERER', 'Charterer Account'),
        ('OWNER', 'Owner Account'),
        ('SHARED', 'Shared'),
    ]

    # Ship Identification
    ship_name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Ship name at the time of this contract"
    )
    imo_number = models.CharField(
        max_length=10,
        db_index=True,
        help_text="IMO number (unique ship identifier, permanent)"
    )
    ship_type = models.CharField(
        max_length=20,
        choices=SHIP_TYPE_CHOICES,
        help_text="Type of vessel"
    )

    # Contract Status
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='ON_TC',
        db_index=True,
        help_text="Current delivery status"
    )
    trade = models.CharField(
        max_length=20,
        choices=TRADE_CHOICES,
        help_text="Type of trade"
    )

    # Owner Information
    owner_name = models.CharField(max_length=200, help_text="Ship owner name")
    owner_email = models.EmailField(blank=True, help_text="Ship owner contact email")

    # Technical Manager Information
    technical_manager = models.CharField(
        max_length=200,
        blank=True,
        help_text="Technical manager name"
    )
    technical_manager_email = models.EmailField(
        blank=True,
        help_text="Technical manager contact email"
    )

    # Charter Details
    charter_length_years = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Charter length in years (e.g., 1.5, 3.0)"
    )
    tc_rate_monthly = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Time charter rate per month in USD"
    )

    # RADAR Integration
    radar_deal_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="RADAR deal number (e.g., A1234567) - must be unique"
    )

    # Important Dates (format: dd/mm/yyyy)
    delivery_date = models.DateField(
        help_text="Actual or expected delivery date"
    )
    redelivery_date = models.DateField(
        help_text="Actual or expected redelivery date"
    )
    tcp_date = models.DateField(
        help_text="Time Charter Party contract date"
    )

    # Broker Information
    broker_name = models.CharField(max_length=200, blank=True, help_text="Broker name")
    broker_email = models.EmailField(blank=True, help_text="Broker contact email")
    broker_commission = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Broker commission in percent (e.g., 1.5, 2.5)"
    )

    # Locations
    delivery_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Delivery port/location"
    )
    redelivery_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Redelivery port/location"
    )

    # Technical Specifications
    bunkers_policy = models.CharField(
        max_length=20,
        choices=BUNKERS_POLICY_CHOICES,
        blank=True,
        help_text="Bunkers policy"
    )
    summer_dwt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Summer deadweight tonnage"
    )
    built_year = models.IntegerField(help_text="Year vessel was built")
    flag = models.CharField(max_length=50, help_text="Vessel flag")
    next_drydock_date = models.DateField(
        null=True,
        blank=True,
        help_text="Next scheduled dry-dock date"
    )

    # Internal Information
    trader_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Freight trader name (from your company)"
    )

    # Additional Notes
    notes = models.TextField(blank=True, help_text="Additional notes")

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'claims.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tc_fleet_created'
    )

    class Meta:
        ordering = ['-delivery_date', 'ship_name']
        verbose_name = 'TC Fleet Contract'
        verbose_name_plural = 'TC Fleet Contracts'
        indexes = [
            models.Index(fields=['imo_number']),  # For grouping contracts by ship
            models.Index(fields=['ship_name']),  # For search
            models.Index(fields=['delivery_status']),  # For filtering by status
            models.Index(fields=['radar_deal_number']),  # For RADAR lookups
            models.Index(fields=['delivery_date']),  # For date-based queries
            models.Index(fields=['redelivery_date']),  # For date-based queries
            models.Index(fields=['ship_type']),  # For filtering by type
            models.Index(fields=['trade']),  # For filtering by trade
            models.Index(fields=['owner_name']),  # For owner analysis
            models.Index(fields=['trader_name']),  # For trader analysis
            models.Index(fields=['delivery_status', 'delivery_date']),  # Common filter combo
            models.Index(fields=['imo_number', 'delivery_date']),  # Ship contract history
        ]

    def __str__(self) -> str:
        return f"{self.ship_name} (IMO: {self.imo_number}) - {self.radar_deal_number}"

    @property
    def contract_status(self) -> str:
        """Calculate current contract status based on dates"""
        today = timezone.now().date()

        if self.delivery_status == 'REDELIVERED':
            return 'COMPLETED'
        elif self.delivery_status == 'INCOMING_TC':
            if self.delivery_date > today:
                return 'INCOMING'
            else:
                return 'ACTIVE'
        elif self.delivery_status == 'ON_TC':
            if self.redelivery_date < today:
                return 'EXPIRED'
            elif (self.redelivery_date - today).days <= 30:
                return 'EXPIRING_SOON'
            else:
                return 'ACTIVE'
        return 'UNKNOWN'

    @property
    def days_remaining(self) -> int:
        """Calculate days remaining until redelivery"""
        if self.delivery_status == 'REDELIVERED':
            return 0
        today = timezone.now().date()
        if self.redelivery_date >= today:
            return (self.redelivery_date - today).days
        return 0

    @property
    def charter_length_months(self) -> float:
        """Calculate charter length in months"""
        return float(self.charter_length_years) * 12

    @property
    def total_contract_value(self) -> Decimal:
        """Calculate total contract value in USD"""
        return self.tc_rate_monthly * Decimal(str(self.charter_length_months))

    def get_ship_master_data(self) -> Optional[Ship]:
        """Get related Ship master data if exists"""
        try:
            return Ship.objects.get(imo_number=self.imo_number)
        except Ship.DoesNotExist:
            return None

    def get_contract_history_for_ship(self) -> QuerySet:
        """Get all TC contracts for this IMO number"""
        return TCFleet.objects.filter(
            imo_number=self.imo_number
        ).order_by('-delivery_date')

    def get_current_ship_name(self) -> Optional[str]:
        """Get current ship name from Ship master data if different"""
        ship = self.get_ship_master_data()
        if ship and ship.vessel_name != self.ship_name:
            return ship.vessel_name
        return None


class ShipSpecification(models.Model):
    """
    Q88 Ship Specifications for TC Fleet vessels.
    Comprehensive technical and operational data for tanker vessels.
    """

    VESSEL_TYPE_CHOICES = [
        ('CRUDE', 'Crude Oil Tanker'),
        ('PRODUCT', 'Product Tanker'),
        ('CHEMICAL', 'Chemical Tanker'),
    ]

    COATING_CHOICES = [
        ('EPOXY', 'Epoxy'),
        ('ZINC', 'Zinc'),
        ('STAINLESS_STEEL', 'Stainless Steel'),
        ('UNCOATED', 'Uncoated'),
    ]

    FUEL_TYPE_CHOICES = [
        ('IFO', 'IFO (Intermediate Fuel Oil)'),
        ('MGO', 'MGO (Marine Gas Oil)'),
        ('VLSFO', 'VLSFO (Very Low Sulfur Fuel Oil)'),
        ('LNG', 'LNG (Liquefied Natural Gas)'),
    ]

    # ============ VESSEL IDENTIFICATION ============
    vessel_name = models.CharField(max_length=200, db_index=True)
    imo_number = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="IMO number - permanent identifier"
    )
    call_sign = models.CharField(max_length=20, blank=True)
    flag = models.CharField(max_length=50)
    port_of_registry = models.CharField(max_length=100, blank=True)
    official_number = models.CharField(max_length=50, blank=True)
    vessel_type = models.CharField(max_length=20, choices=VESSEL_TYPE_CHOICES)
    built_year = models.IntegerField()
    built_country = models.CharField(max_length=100, blank=True)
    shipyard = models.CharField(max_length=200, blank=True)
    classification_society = models.CharField(max_length=100, blank=True)
    class_notation = models.CharField(max_length=200, blank=True)

    # ============ DIMENSIONS & TONNAGES ============
    length_overall = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="LOA in meters"
    )
    length_between_perpendiculars = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="LBP in meters",
        null=True,
        blank=True
    )
    breadth_moulded = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Breadth in meters"
    )
    depth_moulded = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Depth in meters"
    )
    summer_draft = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Summer draft in meters"
    )
    summer_deadweight = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Summer DWT in metric tons"
    )
    lightweight = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Lightweight in metric tons"
    )
    gross_tonnage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Gross tonnage (GT)"
    )
    net_tonnage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Net tonnage (NT)"
    )
    suez_canal_tonnage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    panama_canal_tonnage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ============ CARGO CAPACITY ============
    total_cargo_capacity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total cargo capacity in cubic meters at 98%"
    )
    number_of_cargo_tanks = models.IntegerField()
    segregated_ballast_tanks_capacity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    slop_tank_capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    cargo_tank_coating = models.CharField(max_length=20, choices=COATING_CHOICES)
    cargo_heating_capability = models.BooleanField(default=False)
    maximum_heating_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Maximum heating temperature in Celsius"
    )

    # ============ MACHINERY & PERFORMANCE ============
    main_engine_type = models.CharField(max_length=200)
    main_engine_power = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Power in kW or BHP"
    )
    main_engine_builder = models.CharField(max_length=100, blank=True)
    service_speed_laden = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Service speed laden in knots"
    )
    service_speed_ballast = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Service speed ballast in knots"
    )
    fuel_consumption_laden = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Fuel consumption laden in tons per day"
    )
    fuel_consumption_ballast = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Fuel consumption ballast in tons per day"
    )
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES)
    bow_thruster = models.BooleanField(default=False)
    stern_thruster = models.BooleanField(default=False)

    # ============ CARGO HANDLING ============
    number_of_cargo_pumps = models.IntegerField()
    cargo_pump_capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cargo pump capacity in cubic meters per hour"
    )
    inert_gas_system = models.BooleanField(default=False, help_text="IGS")
    crude_oil_washing = models.BooleanField(default=False, help_text="COW")
    vapor_recovery_system = models.BooleanField(default=False, help_text="VRS")
    cargo_manifold_size = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Manifold size in inches"
    )
    cargo_manifold_pressure_rating = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Pressure rating in bar or psi",
        null=True,
        blank=True
    )

    # ============ ENVIRONMENTAL & SAFETY ============
    double_hull = models.BooleanField(default=True)
    ice_class = models.CharField(max_length=50, blank=True)
    oil_pollution_prevention_certificate_expiry = models.DateField(null=True, blank=True)
    safety_management_certificate_expiry = models.DateField(null=True, blank=True)
    safety_equipment_certificate_expiry = models.DateField(null=True, blank=True)
    international_oil_pollution_certificate_expiry = models.DateField(null=True, blank=True)
    ship_sanitation_certificate_expiry = models.DateField(null=True, blank=True)

    # ============ OPERATIONAL REQUIREMENTS ============
    minimum_freeboard_laden = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Minimum freeboard laden in meters",
        null=True,
        blank=True
    )
    air_draft_ballast = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Air draft ballast in meters",
        null=True,
        blank=True
    )
    air_draft_laden = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Air draft laden in meters",
        null=True,
        blank=True
    )
    maximum_allowed_draft_restriction = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Maximum allowed draft in meters",
        null=True,
        blank=True
    )
    port_restrictions = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)

    # ============ COMMERCIAL ============
    owner_name = models.CharField(max_length=200)
    operator_name = models.CharField(max_length=200, blank=True)
    commercial_manager = models.CharField(max_length=200, blank=True)
    technical_manager = models.CharField(max_length=200)
    p_and_i_club = models.CharField(max_length=200, blank=True, help_text="P&I Club")

    # ============ METADATA ============
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'claims.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ship_specifications'
    )

    class Meta:
        db_table = 'ship_specifications'
        verbose_name = 'Ship Specification (Q88)'
        verbose_name_plural = 'Ship Specifications (Q88)'
        ordering = ['vessel_name']
        indexes = [
            models.Index(fields=['imo_number']),
            models.Index(fields=['vessel_name']),
            models.Index(fields=['vessel_type']),
        ]

    def __str__(self) -> str:
        return f"{self.vessel_name} ({self.imo_number})"

    def get_tc_fleet_contracts(self) -> QuerySet:
        """Get all TC Fleet contracts for this vessel"""
        return TCFleet.objects.filter(imo_number=self.imo_number).order_by('-delivery_date')

    def get_active_tc_contract(self) -> Optional[TCFleet]:
        """Get the currently active TC contract if exists"""
        return TCFleet.objects.filter(
            imo_number=self.imo_number,
            delivery_status='ON_TC'
        ).first()

    @property
    def displacement(self) -> Decimal:
        """Calculate displacement (DWT + Lightweight)"""
        return self.summer_deadweight + self.lightweight

    @property
    def cargo_capacity_per_tank(self) -> Decimal:
        """Calculate average cargo capacity per tank"""
        if self.number_of_cargo_tanks > 0:
            return self.total_cargo_capacity / self.number_of_cargo_tanks
        return Decimal('0')
