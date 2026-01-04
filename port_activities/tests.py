"""
Comprehensive test suite for port_activities app.

Tests cover:
- ActivityType model functionality
- PortActivity model functionality
- Date status tracking (Estimated vs Actual)
- Duration calculations
- Overlap validation
- Cross-app integration with ships and claims
- RADAR sync functionality
- Edge cases and validation
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from port_activities.models import ActivityType, PortActivity
from ships.models import Ship
from claims.models import Voyage, ShipOwner

User = get_user_model()


@pytest.mark.django_db
class TestActivityTypeModel:
    """Test ActivityType model functionality"""

    @pytest.fixture
    def cargo_ops_activity(self):
        """Create a cargo operations activity type"""
        return ActivityType.objects.create(
            code='load_cargo',
            name='Loading Cargo',
            category='CARGO_OPS',
            description='Loading cargo operations',
            icon_class='bi-box-seam',
            color_class='text-primary'
        )

    @pytest.fixture
    def bunkering_activity(self):
        """Create a bunkering activity type"""
        return ActivityType.objects.create(
            code='bunkering',
            name='Bunkering',
            category='BUNKERING',
            description='Fuel bunkering operations',
            icon_class='bi-fuel-pump',
            color_class='text-warning'
        )

    def test_activity_type_creation(self, cargo_ops_activity):
        """Test activity type creation"""
        assert cargo_ops_activity.code == 'load_cargo'
        assert cargo_ops_activity.name == 'Loading Cargo'
        assert cargo_ops_activity.category == 'CARGO_OPS'
        assert cargo_ops_activity.is_active is True

    def test_activity_type_str_representation(self, cargo_ops_activity):
        """Test activity type string representation"""
        expected = "Loading Cargo (Cargo Operations)"
        assert str(cargo_ops_activity) == expected

    def test_code_uniqueness(self, cargo_ops_activity):
        """Test that activity codes must be unique"""
        with pytest.raises(IntegrityError):
            ActivityType.objects.create(
                code='load_cargo',  # Duplicate
                name='Different Name',
                category='CARGO_OPS'
            )

    def test_category_choices(self):
        """Test category choices"""
        categories = [choice[0] for choice in ActivityType.CATEGORY_CHOICES]
        assert 'CARGO_OPS' in categories
        assert 'BUNKERING' in categories
        assert 'MAINTENANCE' in categories
        assert 'OFFHIRE' in categories

    def test_ordering(self, cargo_ops_activity, bunkering_activity):
        """Test default ordering by category and name"""
        # Create another in same category
        ActivityType.objects.create(
            code='discharge_cargo',
            name='Discharging Cargo',
            category='CARGO_OPS'
        )

        activities = list(ActivityType.objects.all())
        # Should be ordered by category, then name
        assert activities[0].category == 'BUNKERING'  # Alphabetically first
        assert activities[1].name == 'Discharging Cargo'  # Within CARGO_OPS
        assert activities[2].name == 'Loading Cargo'

    def test_optional_fields(self):
        """Test that optional fields can be blank"""
        activity = ActivityType.objects.create(
            code='minimal',
            name='Minimal Activity',
            category='OPERATIONAL'
        )
        assert activity.description == ''
        assert activity.icon_class == ''
        assert activity.color_class == ''

    def test_is_active_default(self):
        """Test is_active defaults to True"""
        activity = ActivityType.objects.create(
            code='test_active',
            name='Test Active',
            category='TRANSIT'
        )
        assert activity.is_active is True

    def test_deactivate_activity_type(self, cargo_ops_activity):
        """Test deactivating an activity type"""
        cargo_ops_activity.is_active = False
        cargo_ops_activity.save()

        refreshed = ActivityType.objects.get(pk=cargo_ops_activity.pk)
        assert refreshed.is_active is False


@pytest.mark.django_db
class TestPortActivityModel:
    """Test PortActivity model functionality"""

    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='activityuser',
            email='activity@example.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def ship(self):
        """Create a test ship"""
        return Ship.objects.create(
            imo_number='IMO1234567',
            vessel_name='Activity Test Ship',
            vessel_type='AFRAMAX',
            built_year=2015,
            deadweight=Decimal('105000.00')
        )

    @pytest.fixture
    def ship_owner(self):
        """Create a ship owner"""
        return ShipOwner.objects.create(
            name='Test Ship Owner',
            code='TSO001'
        )

    @pytest.fixture
    def voyage(self, ship_owner, test_user):
        """Create a test voyage"""
        return Voyage.objects.create(
            radar_voyage_id='RADAR-V2024-001',
            voyage_number='V2024-001',
            vessel_name='Activity Test Ship',
            imo_number='IMO1234567',
            ship_owner=ship_owner,
            charter_party='TEST-CP-001',
            load_port='Rotterdam',
            discharge_port='Singapore',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            demurrage_rate=Decimal('25000.00'),
            laytime_allowed=Decimal('72.00'),
            assigned_analyst=test_user
        )

    @pytest.fixture
    def activity_type(self):
        """Create an activity type"""
        return ActivityType.objects.create(
            code='load',
            name='Loading',
            category='CARGO_OPS'
        )

    @pytest.fixture
    def basic_activity(self, ship, activity_type, test_user):
        """Create a basic port activity"""
        now = timezone.now()
        return PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Rotterdam',
            start_datetime=now,
            end_datetime=now + timedelta(hours=24),
            start_date_status='ESTIMATED',
            end_date_status='ESTIMATED',
            created_by=test_user
        )

    @pytest.fixture
    def actual_activity(self, ship, activity_type, test_user):
        """Create an activity with actual dates"""
        now = timezone.now()
        return PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Singapore',
            start_datetime=now + timedelta(days=10),
            end_datetime=now + timedelta(days=10, hours=36),
            start_date_status='ACTUAL',
            end_date_status='ACTUAL',
            created_by=test_user
        )

    def test_activity_creation(self, basic_activity):
        """Test basic activity creation"""
        assert basic_activity.ship.vessel_name == 'Activity Test Ship'
        assert basic_activity.activity_type.name == 'Loading'
        assert basic_activity.port_name == 'Rotterdam'
        assert basic_activity.start_date_status == 'ESTIMATED'
        assert basic_activity.end_date_status == 'ESTIMATED'

    def test_activity_str_representation(self, basic_activity):
        """Test activity string representation"""
        expected = "Activity Test Ship - Loading at Rotterdam"
        assert str(basic_activity) == expected

    def test_duration_auto_calculation(self, basic_activity):
        """Test that duration is automatically calculated"""
        expected_duration = timedelta(hours=24)
        assert basic_activity.duration == expected_duration

    def test_duration_hours_property(self, basic_activity):
        """Test duration_hours property"""
        assert basic_activity.duration_hours == 24.0

    def test_duration_days_property(self, basic_activity):
        """Test duration_days property"""
        assert basic_activity.duration_days == 1

    def test_duration_days_fractional(self, ship, activity_type, test_user):
        """Test duration_days with fractional days"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Test Port',
            start_datetime=now,
            end_datetime=now + timedelta(hours=36),  # 1.5 days
            created_by=test_user
        )
        assert activity.duration_days == 1  # Days only counts full days

    def test_is_fully_actual_true(self, actual_activity):
        """Test is_fully_actual when both dates are actual"""
        assert actual_activity.is_fully_actual is True

    def test_is_fully_actual_false(self, basic_activity):
        """Test is_fully_actual when dates are estimated"""
        assert basic_activity.is_fully_actual is False

    def test_is_fully_estimated_true(self, basic_activity):
        """Test is_fully_estimated when both dates are estimated"""
        assert basic_activity.is_fully_estimated is True

    def test_is_fully_estimated_false(self, actual_activity):
        """Test is_fully_estimated when dates are actual"""
        assert actual_activity.is_fully_estimated is False

    def test_mixed_date_status(self, ship, activity_type, test_user):
        """Test activity with mixed estimated/actual dates"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Mixed Port',
            start_datetime=now,
            start_date_status='ACTUAL',
            end_datetime=now + timedelta(hours=12),
            end_date_status='ESTIMATED',
            created_by=test_user
        )
        assert activity.is_fully_actual is False
        assert activity.is_fully_estimated is False
        assert 'Start: Actual' in activity.date_status_display
        assert 'End: Estimated' in activity.date_status_display

    def test_date_status_display_fully_actual(self, actual_activity):
        """Test date_status_display for fully actual activity"""
        assert actual_activity.date_status_display == "Actual"

    def test_date_status_display_fully_estimated(self, basic_activity):
        """Test date_status_display for fully estimated activity"""
        assert basic_activity.date_status_display == "Estimated"

    def test_end_before_start_validation(self, ship, activity_type, test_user):
        """Test validation that end must be after start"""
        now = timezone.now()
        with pytest.raises(ValidationError, match="End datetime must be after start datetime"):
            PortActivity.objects.create(
                ship=ship,
                activity_type=activity_type,
                port_name='Invalid Dates',
                start_datetime=now,
                end_datetime=now - timedelta(hours=1),  # Before start
                created_by=test_user
            )

    def test_end_equal_to_start_validation(self, ship, activity_type, test_user):
        """Test validation when end equals start"""
        now = timezone.now()
        with pytest.raises(ValidationError, match="End datetime must be after start datetime"):
            PortActivity.objects.create(
                ship=ship,
                activity_type=activity_type,
                port_name='Same Times',
                start_datetime=now,
                end_datetime=now,  # Same as start
                created_by=test_user
            )

    def test_overlap_validation(self, ship, activity_type, test_user, basic_activity):
        """Test validation prevents overlapping activities"""
        # Try to create overlapping activity
        overlap_start = basic_activity.start_datetime + timedelta(hours=12)
        overlap_end = basic_activity.end_datetime + timedelta(hours=12)

        overlapping_activity = PortActivity(
            ship=ship,
            activity_type=activity_type,
            port_name='Overlapping Port',
            start_datetime=overlap_start,
            end_datetime=overlap_end,
            created_by=test_user
        )

        with pytest.raises(ValidationError, match="Activity overlaps"):
            overlapping_activity.clean()

    def test_no_overlap_different_ships(self, ship, activity_type, test_user, basic_activity):
        """Test that overlap validation doesn't apply to different ships"""
        other_ship = Ship.objects.create(
            imo_number='IMO9999999',
            vessel_name='Other Ship',
            vessel_type='VLCC',
            built_year=2020,
            deadweight=Decimal('300000.00')
        )

        # Same time period, different ship - should be allowed
        activity = PortActivity(
            ship=other_ship,
            activity_type=activity_type,
            port_name='Other Port',
            start_datetime=basic_activity.start_datetime,
            end_datetime=basic_activity.end_datetime,
            created_by=test_user
        )

        activity.clean()  # Should not raise
        activity.save()
        assert activity.pk is not None

    def test_no_overlap_consecutive_activities(self, ship, activity_type, test_user, basic_activity):
        """Test consecutive activities don't overlap"""
        # Activity starting exactly when previous ends
        consecutive = PortActivity(
            ship=ship,
            activity_type=activity_type,
            port_name='Next Port',
            start_datetime=basic_activity.end_datetime,
            end_datetime=basic_activity.end_datetime + timedelta(hours=12),
            created_by=test_user
        )

        consecutive.clean()  # Should not raise
        consecutive.save()
        assert consecutive.pk is not None

    def test_activity_with_voyage(self, ship, voyage, activity_type, test_user):
        """Test activity linked to voyage"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            voyage=voyage,
            activity_type=activity_type,
            port_name='Rotterdam',
            load_port='Rotterdam',
            discharge_port='Singapore',
            start_datetime=now,
            end_datetime=now + timedelta(hours=48),
            created_by=test_user
        )

        assert activity.voyage == voyage
        assert activity.load_port == 'Rotterdam'
        assert activity.discharge_port == 'Singapore'

    def test_optional_fields(self, ship, activity_type, test_user):
        """Test optional fields can be blank/null"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Minimal Port',
            start_datetime=now,
            end_datetime=now + timedelta(hours=12),
            created_by=test_user
        )

        assert activity.voyage is None
        assert activity.load_port == ''
        assert activity.discharge_port == ''
        assert activity.cargo_quantity is None
        assert activity.notes == ''
        assert activity.user_comments == ''
        assert activity.radar_activity_id == ''
        assert activity.last_radar_sync is None

    def test_cargo_quantity(self, ship, activity_type, test_user):
        """Test activity with cargo quantity"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Cargo Port',
            start_datetime=now,
            end_datetime=now + timedelta(hours=30),
            cargo_quantity=Decimal('85000.50'),
            created_by=test_user
        )

        assert activity.cargo_quantity == Decimal('85000.50')

    def test_radar_sync_fields(self, ship, activity_type, test_user):
        """Test RADAR sync fields"""
        now = timezone.now()
        sync_time = now - timedelta(hours=1)

        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='RADAR Port',
            start_datetime=now,
            end_datetime=now + timedelta(hours=24),
            radar_activity_id='RADAR-ACT-12345',
            last_radar_sync=sync_time,
            notes='Synced from RADAR system',
            created_by=test_user
        )

        assert activity.radar_activity_id == 'RADAR-ACT-12345'
        assert activity.last_radar_sync == sync_time
        assert 'RADAR' in activity.notes

    def test_user_comments_editable(self, basic_activity):
        """Test user comments can be edited"""
        basic_activity.user_comments = 'Delayed due to weather'
        basic_activity.save()

        refreshed = PortActivity.objects.get(pk=basic_activity.pk)
        assert refreshed.user_comments == 'Delayed due to weather'

    def test_ordering(self, ship, activity_type, test_user):
        """Test default ordering by ship and start_datetime"""
        now = timezone.now()

        activity1 = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Port 1',
            start_datetime=now + timedelta(days=2),
            end_datetime=now + timedelta(days=2, hours=12),
            created_by=test_user
        )

        activity2 = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Port 2',
            start_datetime=now + timedelta(days=1),
            end_datetime=now + timedelta(days=1, hours=12),
            created_by=test_user
        )

        activities = list(PortActivity.objects.all())
        # Should be ordered by ship, then start_datetime
        assert activities[0] == activity2  # Earlier date first
        assert activities[1] == activity1


@pytest.mark.django_db
class TestCrossAppIntegration:
    """Test integration with ships and claims apps"""

    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='integration_user',
            email='integration@example.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def ship(self):
        """Create a test ship"""
        return Ship.objects.create(
            imo_number='IMO1111111',
            vessel_name='Integration Ship',
            vessel_type='SUEZMAX',
            built_year=2018,
            deadweight=Decimal('158000.00')
        )

    @pytest.fixture
    def ship_owner(self):
        """Create a ship owner"""
        return ShipOwner.objects.create(
            name='Integration Owner',
            code='INT001'
        )

    @pytest.fixture
    def voyage(self, ship_owner, test_user):
        """Create a voyage"""
        return Voyage.objects.create(
            radar_voyage_id='RADAR-V2024-INT',
            voyage_number='V2024-INT',
            vessel_name='Integration Ship',
            imo_number='IMO1111111',
            ship_owner=ship_owner,
            charter_party='INT-CP-001',
            load_port='Houston',
            discharge_port='Rotterdam',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=10),
            demurrage_rate=Decimal('30000.00'),
            laytime_allowed=Decimal('96.00'),
            assigned_analyst=test_user
        )

    @pytest.fixture
    def activity_type(self):
        """Create an activity type"""
        return ActivityType.objects.create(
            code='discharge',
            name='Discharging',
            category='CARGO_OPS'
        )

    def test_ship_port_activities_relation(self, ship, activity_type, test_user):
        """Test accessing port activities through ship"""
        now = timezone.now()

        activity1 = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Port A',
            start_datetime=now,
            end_datetime=now + timedelta(hours=24),
            created_by=test_user
        )

        activity2 = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Port B',
            start_datetime=now + timedelta(days=5),
            end_datetime=now + timedelta(days=5, hours=18),
            created_by=test_user
        )

        # Access through ship's reverse relation
        ship_activities = ship.port_activities.all()
        assert ship_activities.count() == 2
        assert activity1 in ship_activities
        assert activity2 in ship_activities

    def test_voyage_port_activities_relation(self, ship, voyage, activity_type, test_user):
        """Test accessing port activities through voyage"""
        now = timezone.now()

        activity1 = PortActivity.objects.create(
            ship=ship,
            voyage=voyage,
            activity_type=activity_type,
            port_name='Houston',
            start_datetime=now,
            end_datetime=now + timedelta(hours=36),
            created_by=test_user
        )

        activity2 = PortActivity.objects.create(
            ship=ship,
            voyage=voyage,
            activity_type=activity_type,
            port_name='Rotterdam',
            start_datetime=now + timedelta(days=15),
            end_datetime=now + timedelta(days=15, hours=42),
            created_by=test_user
        )

        # Access through voyage's reverse relation
        voyage_activities = voyage.port_activities.all()
        assert voyage_activities.count() == 2
        assert activity1 in voyage_activities
        assert activity2 in voyage_activities

    def test_activity_type_protect_on_delete(self, ship, activity_type, test_user):
        """Test that deleting activity type is protected"""
        now = timezone.now()
        PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Protected Port',
            start_datetime=now,
            end_datetime=now + timedelta(hours=12),
            created_by=test_user
        )

        # Should not be able to delete activity type
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            activity_type.delete()

    def test_ship_protect_on_delete(self, ship, activity_type, test_user):
        """Test that deleting ship is protected when activities exist"""
        now = timezone.now()
        PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Ship Protected',
            start_datetime=now,
            end_datetime=now + timedelta(hours=12),
            created_by=test_user
        )

        # Should not be able to delete ship
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            ship.delete()

    def test_voyage_set_null_on_delete(self, ship, voyage, activity_type, test_user):
        """Test that deleting voyage sets activity voyage to null"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            voyage=voyage,
            activity_type=activity_type,
            port_name='Voyage Null Test',
            start_datetime=now,
            end_datetime=now + timedelta(hours=24),
            created_by=test_user
        )

        voyage_id = voyage.id
        voyage.delete()

        # Activity should still exist but voyage should be null
        activity.refresh_from_db()
        assert activity.voyage is None
        assert activity.pk is not None

    def test_multiple_activities_same_voyage(self, ship, voyage, test_user):
        """Test multiple activities for same voyage"""
        load_type = ActivityType.objects.create(
            code='load_multi',
            name='Loading Multi',
            category='CARGO_OPS'
        )

        discharge_type = ActivityType.objects.create(
            code='discharge_multi',
            name='Discharging Multi',
            category='CARGO_OPS'
        )

        now = timezone.now()

        load_activity = PortActivity.objects.create(
            ship=ship,
            voyage=voyage,
            activity_type=load_type,
            port_name='Houston',
            start_datetime=now,
            end_datetime=now + timedelta(hours=36),
            created_by=test_user
        )

        discharge_activity = PortActivity.objects.create(
            ship=ship,
            voyage=voyage,
            activity_type=discharge_type,
            port_name='Rotterdam',
            start_datetime=now + timedelta(days=15),
            end_datetime=now + timedelta(days=15, hours=42),
            created_by=test_user
        )

        voyage_activities = list(voyage.port_activities.order_by('start_datetime'))
        assert len(voyage_activities) == 2
        assert voyage_activities[0] == load_activity
        assert voyage_activities[1] == discharge_activity


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='edge_user',
            email='edge@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def ship(self):
        """Create a test ship"""
        return Ship.objects.create(
            imo_number='IMO9999999',
            vessel_name='Edge Case Ship',
            vessel_type='PANAMAX',
            built_year=2016,
            deadweight=Decimal('75000.00')
        )

    @pytest.fixture
    def activity_type(self):
        """Create an activity type"""
        return ActivityType.objects.create(
            code='edge_test',
            name='Edge Test',
            category='OPERATIONAL'
        )

    def test_very_short_duration(self, ship, activity_type, test_user):
        """Test activity with very short duration (1 minute)"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Quick Port',
            start_datetime=now,
            end_datetime=now + timedelta(minutes=1),
            created_by=test_user
        )

        assert activity.duration_hours == pytest.approx(1/60, rel=1e-3)
        assert activity.duration_days == 0

    def test_very_long_duration(self, ship, activity_type, test_user):
        """Test activity with very long duration (30 days)"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Long Port',
            start_datetime=now,
            end_datetime=now + timedelta(days=30),
            created_by=test_user
        )

        assert activity.duration_hours == 720.0  # 30 * 24
        assert activity.duration_days == 30

    def test_zero_cargo_quantity(self, ship, activity_type, test_user):
        """Test activity with zero cargo quantity"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Zero Cargo',
            start_datetime=now,
            end_datetime=now + timedelta(hours=12),
            cargo_quantity=Decimal('0.00'),
            created_by=test_user
        )

        assert activity.cargo_quantity == Decimal('0.00')

    def test_very_large_cargo_quantity(self, ship, activity_type, test_user):
        """Test activity with large cargo quantity"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Large Cargo',
            start_datetime=now,
            end_datetime=now + timedelta(hours=48),
            cargo_quantity=Decimal('99999999.99'),  # Max for decimal(10,2)
            created_by=test_user
        )

        assert activity.cargo_quantity == Decimal('99999999.99')

    def test_update_existing_activity_dates(self, ship, activity_type, test_user):
        """Test updating dates of existing activity"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Update Port',
            start_datetime=now,
            end_datetime=now + timedelta(hours=24),
            created_by=test_user
        )

        original_duration = activity.duration

        # Update dates
        activity.start_datetime = now + timedelta(hours=2)
        activity.end_datetime = now + timedelta(hours=30)
        activity.save()

        activity.refresh_from_db()
        assert activity.duration != original_duration
        assert activity.duration == timedelta(hours=28)

    def test_change_date_status(self, ship, activity_type, test_user):
        """Test changing from estimated to actual"""
        now = timezone.now()
        activity = PortActivity.objects.create(
            ship=ship,
            activity_type=activity_type,
            port_name='Status Change',
            start_datetime=now,
            end_datetime=now + timedelta(hours=20),
            start_date_status='ESTIMATED',
            end_date_status='ESTIMATED',
            created_by=test_user
        )

        assert activity.is_fully_estimated is True

        # Change to actual
        activity.start_date_status = 'ACTUAL'
        activity.end_date_status = 'ACTUAL'
        activity.save()

        activity.refresh_from_db()
        assert activity.is_fully_actual is True
        assert activity.is_fully_estimated is False
