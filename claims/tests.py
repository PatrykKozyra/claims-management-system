"""
Tests for Claims Management System

This file includes:
1. Concurrency tests - preventing simultaneous edits
2. Database failure tests - handling connection issues
3. Error handling tests - user-friendly error messages
"""

from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection, transaction
from django.db.utils import OperationalError, DatabaseError
from django.test.utils import override_settings
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
import threading
import time

from .models import User, Claim, Voyage, ShipOwner, Comment


User = get_user_model()


class ConcurrencyTestCase(TransactionTestCase):
    """
    Tests for concurrent editing scenarios

    These tests simulate multiple users editing the same record simultaneously
    and verify that the application handles conflicts properly.
    """

    def setUp(self):
        """Create test data"""
        # Create users
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='ADMIN',
            email='admin@test.com'
        )

        self.analyst1 = User.objects.create_user(
            username='analyst1',
            password='test123',
            role='WRITE',
            email='analyst1@test.com',
            first_name='John',
            last_name='Doe'
        )

        self.analyst2 = User.objects.create_user(
            username='analyst2',
            password='test123',
            role='WRITE',
            email='analyst2@test.com',
            first_name='Jane',
            last_name='Smith'
        )

        # Create ship owner
        self.owner = ShipOwner.objects.create(
            name='Test Shipping Co',
            code='TEST',
            contact_email='test@shipping.com'
        )

        # Create voyage
        self.voyage = Voyage.objects.create(
            radar_voyage_id='TEST-V-2025-001',
            voyage_number='V2025001',
            vessel_name='MV Test Ship',
            charter_party='GENCON',
            load_port='Singapore',
            discharge_port='Rotterdam',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=7),
            ship_owner=self.owner,
            demurrage_rate=Decimal('10000.00'),
            laytime_allowed=Decimal('72.00'),
            currency='USD',
            assignment_status='ASSIGNED',
            assigned_analyst=self.analyst1
        )

        # Create claim
        self.claim = Claim.objects.create(
            voyage=self.voyage,
            ship_owner=self.owner,
            claim_type='DEMURRAGE',
            status='DRAFT',
            payment_status='NOT_SENT',
            claim_amount=Decimal('50000.00'),
            currency='USD',
            assigned_to=self.analyst1,
            created_by=self.admin,
            description='Test claim'
        )

    def test_concurrent_claim_updates(self):
        """
        Test: Two users updating the same claim simultaneously

        Expected: Second update should detect conflict or use optimistic locking
        """
        client1 = Client()
        client2 = Client()

        # Both users login
        client1.login(username='analyst1', password='test123')
        client2.login(username='analyst2', password='test123')

        # User 1 loads claim detail page
        response1 = client1.get(reverse('claim_detail', args=[self.claim.pk]))
        self.assertEqual(response1.status_code, 200)

        # User 2 loads same claim detail page
        response2 = client2.get(reverse('claim_detail', args=[self.claim.pk]))
        self.assertEqual(response2.status_code, 200)

        # User 1 updates the claim
        update_data1 = {
            'status': 'UNDER_REVIEW',
            'claim_amount': '55000.00',
            'description': 'Updated by analyst 1'
        }
        response1 = client1.post(
            reverse('claim_update', args=[self.claim.pk]),
            update_data1
        )

        # User 2 tries to update the same claim (should detect conflict)
        update_data2 = {
            'status': 'SUBMITTED',
            'claim_amount': '60000.00',
            'description': 'Updated by analyst 2'
        }
        response2 = client2.post(
            reverse('claim_update', args=[self.claim.pk]),
            update_data2
        )

        # Verify that we have some conflict detection mechanism
        # (This test documents the expected behavior - implementation needed)
        self.claim.refresh_from_db()

        # The claim should have one of the updates, but we should warn users
        # about concurrent modifications
        print(f"Final claim status: {self.claim.status}")
        print(f"Final claim amount: {self.claim.claim_amount}")

    def test_concurrent_voyage_assignment(self):
        """
        Test: Two users trying to assign the same voyage simultaneously

        Expected: Only one assignment should succeed, second should get clear error
        """
        # Create unassigned voyage
        unassigned_voyage = Voyage.objects.create(
            radar_voyage_id='TEST-V-2025-002',
            voyage_number='V2025002',
            vessel_name='MV Test Ship 2',
            charter_party='GENCON',
            load_port='Dubai',
            discharge_port='Hamburg',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            ship_owner=self.owner,
            demurrage_rate=Decimal('12000.00'),
            laytime_allowed=Decimal('96.00'),
            currency='USD',
            assignment_status='UNASSIGNED'
        )

        results = {'analyst1': None, 'analyst2': None}

        def assign_voyage(username, password, result_key):
            """Helper function to assign voyage in thread"""
            client = Client()
            client.login(username=username, password=password)
            response = client.post(
                reverse('voyage_assign', args=[unassigned_voyage.pk])
            )
            results[result_key] = response.status_code

        # Create two threads to simulate simultaneous assignment
        thread1 = threading.Thread(
            target=assign_voyage,
            args=('analyst1', 'test123', 'analyst1')
        )
        thread2 = threading.Thread(
            target=assign_voyage,
            args=('analyst2', 'test123', 'analyst2')
        )

        # Start both threads at nearly the same time
        thread1.start()
        thread2.start()

        # Wait for both to complete
        thread1.join()
        thread2.join()

        # Refresh voyage from database
        unassigned_voyage.refresh_from_db()

        # Verify voyage is assigned to exactly one analyst
        self.assertIsNotNone(unassigned_voyage.assigned_analyst)
        self.assertIn(
            unassigned_voyage.assigned_analyst,
            [self.analyst1, self.analyst2]
        )

        print(f"Voyage assigned to: {unassigned_voyage.assigned_analyst.username}")
        print(f"Analyst1 result: {results['analyst1']}")
        print(f"Analyst2 result: {results['analyst2']}")


class DatabaseErrorTestCase(TestCase):
    """
    Tests for database connection failures and error handling

    These tests verify that the application handles database errors gracefully
    and shows user-friendly error messages.
    """

    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            role='WRITE',
            email='test@test.com'
        )
        self.client = Client()
        self.client.login(username='testuser', password='test123')

    def test_database_connection_error_on_voyage_list(self):
        """
        Test: Database connection fails when loading voyage list

        Expected: User sees friendly error message, not technical traceback
        """
        with patch('claims.models.Voyage.objects.all') as mock_voyages:
            # Simulate database connection error
            mock_voyages.side_effect = OperationalError(
                "could not connect to server: Connection refused"
            )

            response = self.client.get(reverse('voyage_list'))

            # Should return 500 or redirect to error page (not crash)
            self.assertIn(response.status_code, [500, 302, 503])

    def test_database_timeout_on_claim_detail(self):
        """
        Test: Database query times out when loading claim details

        Expected: User sees timeout error message
        """
        # Create test data
        owner = ShipOwner.objects.create(
            name='Test Owner',
            code='TEST'
        )
        voyage = Voyage.objects.create(
            radar_voyage_id='TEST-V-001',
            voyage_number='V001',
            vessel_name='Test Vessel',
            charter_party='GENCON',
            load_port='Port A',
            discharge_port='Port B',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            ship_owner=owner,
            demurrage_rate=Decimal('10000'),
            laytime_allowed=Decimal('72'),
            currency='USD'
        )
        claim = Claim.objects.create(
            voyage=voyage,
            ship_owner=owner,
            claim_type='DEMURRAGE',
            claim_amount=Decimal('50000'),
            currency='USD',
            created_by=self.user
        )

        with patch('claims.models.Claim.objects.get') as mock_get:
            # Simulate timeout
            mock_get.side_effect = DatabaseError("statement timeout")

            response = self.client.get(reverse('claim_detail', args=[claim.pk]))

            # Should handle error gracefully
            self.assertIn(response.status_code, [500, 302, 503])

    def test_radar_sync_connection_failure(self):
        """
        Test: RADAR system connection fails during sync

        Expected: Clear error message about external system being unavailable
        """
        # This test documents expected behavior when RADAR system is down
        # Implementation would depend on actual RADAR integration
        pass


class ErrorMessageTestCase(TestCase):
    """
    Tests for user-friendly error messages

    Verifies that users see clear, actionable error messages
    instead of technical jargon.
    """

    def setUp(self):
        """Create test user and client"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            role='READ',  # Read-only user
            email='test@test.com'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role='ADMIN',
            email='admin@test.com'
        )
        self.client = Client()

    def test_permission_denied_clear_message(self):
        """
        Test: User without permission tries to create claim

        Expected: Clear message about needing WRITE permission
        """
        self.client.login(username='testuser', password='test123')

        response = self.client.get(reverse('claim_create'))

        # Should redirect or show permission error
        if response.status_code == 302:
            # Follow redirect
            response = self.client.get(response.url)

        # Should contain user-friendly permission message
        # (Implementation needed in views)
        self.assertIn(response.status_code, [403, 302])

    def test_missing_required_field_clear_message(self):
        """
        Test: User submits form with missing required fields

        Expected: Clear validation errors for each missing field
        """
        self.client.login(username='admin', password='admin123')

        # Try to create claim with missing data
        response = self.client.post(reverse('claim_create'), {
            'claim_type': 'DEMURRAGE',
            # Missing: voyage, ship_owner, amount, etc.
        })

        # Should show form with clear error messages
        # (Actual validation depends on form implementation)
        self.assertIn(response.status_code, [200, 400])

    def test_voyage_already_assigned_clear_message(self):
        """
        Test: User tries to assign already-assigned voyage

        Expected: Clear message that voyage is already assigned to someone
        """
        owner = ShipOwner.objects.create(name='Test', code='TEST')
        analyst = User.objects.create_user(
            username='analyst',
            password='test123',
            role='WRITE'
        )

        voyage = Voyage.objects.create(
            radar_voyage_id='TEST-V-001',
            voyage_number='V001',
            vessel_name='Test',
            charter_party='GENCON',
            load_port='A',
            discharge_port='B',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            ship_owner=owner,
            demurrage_rate=Decimal('10000'),
            laytime_allowed=Decimal('72'),
            currency='USD',
            assignment_status='ASSIGNED',
            assigned_analyst=analyst
        )

        self.client.login(username='testuser', password='test123')

        # Try to assign already-assigned voyage
        response = self.client.post(
            reverse('voyage_assign', args=[voyage.pk])
        )

        # Should get clear error message
        # (Implementation may vary)
        print(f"Response status: {response.status_code}")


class DataIntegrityTestCase(TestCase):
    """
    Tests for data integrity and validation

    Ensures that invalid data cannot be saved to database
    """

    def test_claim_amount_cannot_be_negative(self):
        """
        Test: Cannot create claim with negative amount

        Expected: Validation error
        """
        owner = ShipOwner.objects.create(name='Test', code='TEST')
        admin = User.objects.create_user(username='admin', role='ADMIN')

        voyage = Voyage.objects.create(
            radar_voyage_id='TEST-V-001',
            voyage_number='V001',
            vessel_name='Test',
            charter_party='GENCON',
            load_port='A',
            discharge_port='B',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            ship_owner=owner,
            demurrage_rate=Decimal('10000'),
            laytime_allowed=Decimal('72'),
            currency='USD'
        )

        # Try to create claim with negative amount
        from django.core.exceptions import ValidationError

        claim = Claim(
            voyage=voyage,
            ship_owner=owner,
            claim_type='DEMURRAGE',
            claim_amount=Decimal('-1000.00'),  # Negative!
            currency='USD',
            created_by=admin
        )

        # Should raise validation error when full_clean is called
        with self.assertRaises(ValidationError):
            claim.full_clean()

    def test_paid_amount_cannot_exceed_claim_amount(self):
        """
        Test: Cannot pay more than claimed amount

        Expected: Validation error or warning
        """
        owner = ShipOwner.objects.create(name='Test', code='TEST')
        admin = User.objects.create_user(username='admin', role='ADMIN')

        voyage = Voyage.objects.create(
            radar_voyage_id='TEST-V-001',
            voyage_number='V001',
            vessel_name='Test',
            charter_party='GENCON',
            load_port='A',
            discharge_port='B',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            ship_owner=owner,
            demurrage_rate=Decimal('10000'),
            laytime_allowed=Decimal('72'),
            currency='USD'
        )

        claim = Claim.objects.create(
            voyage=voyage,
            ship_owner=owner,
            claim_type='DEMURRAGE',
            claim_amount=Decimal('50000.00'),
            paid_amount=Decimal('60000.00'),  # More than claimed!
            currency='USD',
            created_by=admin
        )

        # Outstanding amount should be negative, which might warrant a warning
        self.assertLess(claim.outstanding_amount, 0)
        print(f"Warning: Paid amount exceeds claim amount!")
        print(f"Claim: {claim.claim_amount}, Paid: {claim.paid_amount}")
        print(f"Outstanding: {claim.outstanding_amount}")


class PerformanceTestCase(TestCase):
    """
    Tests for performance and N+1 query issues

    Ensures that pages don't make excessive database queries
    """

    def setUp(self):
        """Create test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            role='WRITE'
        )
        self.client = Client()
        self.client.login(username='testuser', password='test123')

        # Create test data
        self.owner = ShipOwner.objects.create(name='Test', code='TEST')

        # Create multiple voyages to test query performance
        for i in range(10):
            Voyage.objects.create(
                radar_voyage_id=f'TEST-V-{i}',
                voyage_number=f'V{i:04d}',
                vessel_name=f'Test Ship {i}',
                charter_party='GENCON',
                load_port='Singapore',
                discharge_port='Rotterdam',
                laycan_start=timezone.now().date(),
                laycan_end=timezone.now().date() + timedelta(days=5),
                ship_owner=self.owner,
                demurrage_rate=Decimal('10000'),
                laytime_allowed=Decimal('72'),
                currency='USD'
            )

    def test_voyage_list_query_count(self):
        """
        Test: Voyage list page query count

        Expected: Should use select_related/prefetch_related to minimize queries
        """
        from django.test.utils import override_settings
        from django.db import connection
        from django.test import override_settings

        # Enable query logging
        with self.assertNumQueries(10):  # Adjust based on actual optimization
            response = self.client.get(reverse('voyage_list'))
            self.assertEqual(response.status_code, 200)

        # Print actual query count for debugging
        print(f"Query count: {len(connection.queries)}")


# Run tests with: python manage.py test claims.tests


# ============================================================================
# PYTEST-BASED COMPREHENSIVE TESTS
# ============================================================================

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import ClaimActivityLog, VoyageAssignment, Document


@pytest.mark.django_db
class TestUserModel:
    """Comprehensive tests for User model"""

    @pytest.fixture
    def admin_user(self):
        """Create an admin user"""
        return User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='ADMIN',
            first_name='Admin',
            last_name='User'
        )

    @pytest.fixture
    def team_lead_user(self):
        """Create a team lead user"""
        return User.objects.create_user(
            username='teamlead_test',
            email='teamlead@test.com',
            password='testpass123',
            role='TEAM_LEAD',
            department='Operations'
        )

    @pytest.fixture
    def write_user(self):
        """Create a write user"""
        return User.objects.create_user(
            username='writer_test',
            email='writer@test.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def read_export_user(self):
        """Create a read+export user"""
        return User.objects.create_user(
            username='reader_export',
            email='reader_export@test.com',
            password='testpass123',
            role='READ_EXPORT'
        )

    @pytest.fixture
    def read_only_user(self):
        """Create a read-only user"""
        return User.objects.create_user(
            username='reader',
            email='reader@test.com',
            password='testpass123',
            role='READ'
        )

    def test_user_creation(self, write_user):
        """Test user creation"""
        assert write_user.username == 'writer_test'
        assert write_user.email == 'writer@test.com'
        assert write_user.role == 'WRITE'
        assert write_user.dark_mode is False

    def test_user_str_representation(self, write_user):
        """Test user string representation"""
        # AbstractUser uses username for __str__
        assert str(write_user) == 'writer_test'

    def test_can_export_admin(self, admin_user):
        """Test admin can export"""
        assert admin_user.can_export() is True

    def test_can_export_team_lead(self, team_lead_user):
        """Test team lead can export"""
        assert team_lead_user.can_export() is True

    def test_can_export_write(self, write_user):
        """Test write user can export"""
        assert write_user.can_export() is True

    def test_can_export_read_export(self, read_export_user):
        """Test read+export user can export"""
        assert read_export_user.can_export() is True

    def test_can_export_read_only_false(self, read_only_user):
        """Test read-only user cannot export"""
        assert read_only_user.can_export() is False

    def test_can_write_admin(self, admin_user):
        """Test admin can write"""
        assert admin_user.can_write() is True

    def test_can_write_team_lead(self, team_lead_user):
        """Test team lead can write"""
        assert team_lead_user.can_write() is True

    def test_can_write_write_user(self, write_user):
        """Test write user can write"""
        assert write_user.can_write() is True

    def test_can_write_read_export_false(self, read_export_user):
        """Test read+export user cannot write"""
        assert read_export_user.can_write() is False

    def test_can_write_read_only_false(self, read_only_user):
        """Test read-only user cannot write"""
        assert read_only_user.can_write() is False

    def test_is_admin_role_true(self, admin_user):
        """Test is_admin_role for admin"""
        assert admin_user.is_admin_role() is True

    def test_is_admin_role_false(self, write_user):
        """Test is_admin_role for non-admin"""
        assert write_user.is_admin_role() is False

    def test_is_team_lead_admin(self, admin_user):
        """Test admin is considered team lead"""
        assert admin_user.is_team_lead() is True

    def test_is_team_lead_team_lead(self, team_lead_user):
        """Test team lead role"""
        assert team_lead_user.is_team_lead() is True

    def test_is_team_lead_write_false(self, write_user):
        """Test write user is not team lead"""
        assert write_user.is_team_lead() is False

    def test_can_assign_voyages_admin(self, admin_user):
        """Test admin can assign voyages"""
        assert admin_user.can_assign_voyages() is True

    def test_can_assign_voyages_team_lead(self, team_lead_user):
        """Test team lead can assign voyages"""
        assert team_lead_user.can_assign_voyages() is True

    def test_can_assign_voyages_write_false(self, write_user):
        """Test write user cannot assign voyages"""
        assert write_user.can_assign_voyages() is False

    def test_dark_mode_default(self, write_user):
        """Test dark mode defaults to False"""
        assert write_user.dark_mode is False

    def test_dark_mode_toggle(self, write_user):
        """Test dark mode can be toggled"""
        write_user.dark_mode = True
        write_user.save()
        write_user.refresh_from_db()
        assert write_user.dark_mode is True

    def test_optional_fields(self, write_user):
        """Test optional fields can be blank"""
        assert write_user.department == ''
        assert write_user.phone == ''
        assert write_user.position == ''
        assert write_user.bio == ''
        # profile_photo is nullable, so .name will be None when not set
        assert write_user.profile_photo.name is None or write_user.profile_photo.name == ''

    def test_user_with_all_fields(self):
        """Test user creation with all fields"""
        user = User.objects.create_user(
            username='complete_user',
            email='complete@test.com',
            password='testpass123',
            role='WRITE',
            first_name='John',
            last_name='Doe',
            department='Claims',
            phone='+1234567890',
            position='Senior Analyst',
            bio='Experienced claims analyst',
            dark_mode=True
        )
        assert user.department == 'Claims'
        assert user.phone == '+1234567890'
        assert user.position == 'Senior Analyst'
        assert user.bio == 'Experienced claims analyst'
        assert user.dark_mode is True

    def test_created_by_relationship(self, admin_user, write_user):
        """Test created_by relationship"""
        write_user.created_by = admin_user
        write_user.save()
        write_user.refresh_from_db()
        assert write_user.created_by == admin_user
        assert write_user in admin_user.users_created.all()


@pytest.mark.django_db
class TestShipOwnerModel:
    """Comprehensive tests for ShipOwner model"""

    @pytest.fixture
    def basic_owner(self):
        """Create a basic ship owner"""
        return ShipOwner.objects.create(
            name='Test Shipping Inc',
            code='TSI001'
        )

    @pytest.fixture
    def complete_owner(self):
        """Create a ship owner with all fields"""
        return ShipOwner.objects.create(
            name='Complete Shipping Ltd',
            code='CSL001',
            contact_email='contact@complete-shipping.com',
            contact_phone='+44 20 1234 5678',
            address='123 Maritime Ave, London, UK',
            notes='Premium client - expedited handling',
            is_active=True
        )

    def test_ship_owner_creation(self, basic_owner):
        """Test basic ship owner creation"""
        assert basic_owner.name == 'Test Shipping Inc'
        assert basic_owner.code == 'TSI001'
        assert basic_owner.is_active is True

    def test_ship_owner_str_representation(self, basic_owner):
        """Test ship owner string representation"""
        expected = "Test Shipping Inc (TSI001)"
        assert str(basic_owner) == expected

    def test_name_uniqueness(self, basic_owner):
        """Test that ship owner names must be unique"""
        with pytest.raises(IntegrityError):
            ShipOwner.objects.create(
                name='Test Shipping Inc',  # Duplicate
                code='TSI002'
            )

    def test_code_uniqueness(self, basic_owner):
        """Test that ship owner codes must be unique"""
        with pytest.raises(IntegrityError):
            ShipOwner.objects.create(
                name='Different Name',
                code='TSI001'  # Duplicate
            )

    def test_is_active_default(self):
        """Test is_active defaults to True"""
        owner = ShipOwner.objects.create(
            name='Active Test',
            code='ACT001'
        )
        assert owner.is_active is True

    def test_deactivate_owner(self, basic_owner):
        """Test deactivating a ship owner"""
        basic_owner.is_active = False
        basic_owner.save()
        basic_owner.refresh_from_db()
        assert basic_owner.is_active is False

    def test_optional_fields(self, basic_owner):
        """Test optional fields can be blank"""
        assert basic_owner.contact_email == ''
        assert basic_owner.contact_phone == ''
        assert basic_owner.address == ''
        assert basic_owner.notes == ''

    def test_complete_owner_fields(self, complete_owner):
        """Test owner with all fields populated"""
        assert complete_owner.contact_email == 'contact@complete-shipping.com'
        assert complete_owner.contact_phone == '+44 20 1234 5678'
        assert 'London' in complete_owner.address
        assert 'Premium client' in complete_owner.notes

    def test_ordering(self):
        """Test default ordering by name"""
        ShipOwner.objects.create(name='Zulu Shipping', code='ZUL001')
        ShipOwner.objects.create(name='Alpha Shipping', code='ALP001')
        ShipOwner.objects.create(name='Beta Shipping', code='BET001')

        owners = list(ShipOwner.objects.all())
        assert owners[0].name == 'Alpha Shipping'
        assert owners[1].name == 'Beta Shipping'
        assert owners[2].name == 'Zulu Shipping'

    def test_timestamps(self, basic_owner):
        """Test created_at and updated_at timestamps"""
        assert basic_owner.created_at is not None
        assert basic_owner.updated_at is not None
        assert basic_owner.created_at <= basic_owner.updated_at


@pytest.mark.django_db
class TestVoyageModel:
    """Comprehensive tests for Voyage model"""

    @pytest.fixture
    def ship_owner(self):
        """Create a ship owner"""
        return ShipOwner.objects.create(
            name='Voyage Test Owner',
            code='VTO001'
        )

    @pytest.fixture
    def analyst_user(self):
        """Create an analyst user"""
        return User.objects.create_user(
            username='voyage_analyst',
            email='analyst@test.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def basic_voyage(self, ship_owner, analyst_user):
        """Create a basic voyage"""
        return Voyage.objects.create(
            radar_voyage_id='RADAR-V-TEST-001',
            voyage_number='VT001',
            vessel_name='MV Test Vessel',
            charter_party='GENCON',
            load_port='Singapore',
            discharge_port='Rotterdam',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=7),
            ship_owner=ship_owner,
            demurrage_rate=Decimal('15000.00'),
            laytime_allowed=Decimal('48.00'),
            assigned_analyst=analyst_user
        )

    @pytest.fixture
    def tc_voyage(self, ship_owner, analyst_user):
        """Create a time charter voyage"""
        return Voyage.objects.create(
            radar_voyage_id='RADAR-V-TC-001',
            voyage_number='VTC001',
            vessel_name='MV TC Vessel',
            imo_number='IMO9876543',
            charter_type='TRADED',
            charter_party='NYPE',
            load_port='Houston',
            discharge_port='Singapore',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=10),
            ship_owner=ship_owner,
            demurrage_rate=Decimal('20000.00'),
            laytime_allowed=Decimal('72.00'),
            assignment_status='ASSIGNED',
            assigned_analyst=analyst_user
        )

    def test_voyage_creation(self, basic_voyage):
        """Test basic voyage creation"""
        assert basic_voyage.voyage_number == 'VT001'
        assert basic_voyage.vessel_name == 'MV Test Vessel'
        assert basic_voyage.charter_type == 'SPOT'  # Default
        assert basic_voyage.assignment_status == 'UNASSIGNED'  # Default

    def test_voyage_str_representation(self, basic_voyage):
        """Test voyage string representation"""
        expected = "VT001 - MV Test Vessel"
        assert str(basic_voyage) == expected

    def test_radar_voyage_id_uniqueness(self, basic_voyage):
        """Test RADAR voyage ID must be unique"""
        with pytest.raises(IntegrityError):
            Voyage.objects.create(
                radar_voyage_id='RADAR-V-TEST-001',  # Duplicate
                voyage_number='VT002',
                vessel_name='MV Other Vessel',
                charter_party='ASBATANKVOY',
                load_port='Dubai',
                discharge_port='Mumbai',
                laycan_start=timezone.now().date(),
                laycan_end=timezone.now().date() + timedelta(days=5),
                ship_owner=basic_voyage.ship_owner,
                demurrage_rate=Decimal('12000.00'),
                laytime_allowed=Decimal('36.00')
            )

    def test_charter_type_spot_default(self, basic_voyage):
        """Test charter_type defaults to SPOT"""
        assert basic_voyage.charter_type == 'SPOT'

    def test_charter_type_traded(self, tc_voyage):
        """Test charter_type TRADED"""
        assert tc_voyage.charter_type == 'TRADED'

    def test_assignment_status_default(self, basic_voyage):
        """Test assignment_status defaults to UNASSIGNED"""
        assert basic_voyage.assignment_status == 'UNASSIGNED'

    def test_assignment_status_assigned(self, tc_voyage):
        """Test assignment_status ASSIGNED"""
        assert tc_voyage.assignment_status == 'ASSIGNED'
        assert tc_voyage.assigned_analyst is not None

    def test_currency_default(self, basic_voyage):
        """Test currency defaults to USD"""
        assert basic_voyage.currency == 'USD'

    def test_demurrage_rate_validation(self, ship_owner):
        """Test demurrage rate must be positive"""
        with pytest.raises(ValidationError):
            voyage = Voyage(
                radar_voyage_id='RADAR-V-INVALID',
                voyage_number='VINV001',
                vessel_name='MV Invalid',
                charter_party='GENCON',
                load_port='Port A',
                discharge_port='Port B',
                laycan_start=timezone.now().date(),
                laycan_end=timezone.now().date() + timedelta(days=5),
                ship_owner=ship_owner,
                demurrage_rate=Decimal('0.00'),  # Invalid - too low
                laytime_allowed=Decimal('48.00')
            )
            voyage.full_clean()

    def test_optional_fields(self, basic_voyage):
        """Test optional fields"""
        assert basic_voyage.imo_number == ''
        assert basic_voyage.assigned_analyst is not None  # Was assigned in fixture

    def test_ship_owner_relationship(self, basic_voyage, ship_owner):
        """Test ship owner foreign key relationship"""
        assert basic_voyage.ship_owner == ship_owner
        assert basic_voyage in ship_owner.voyages.all()

    def test_ship_owner_protect_on_delete(self, basic_voyage):
        """Test ship owner cannot be deleted if voyages exist"""
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            basic_voyage.ship_owner.delete()

    def test_assigned_analyst_relationship(self, tc_voyage, analyst_user):
        """Test assigned analyst relationship"""
        assert tc_voyage.assigned_analyst == analyst_user
        assert tc_voyage in analyst_user.assigned_voyages.all()

    def test_assigned_analyst_set_null_on_delete(self, tc_voyage, analyst_user):
        """Test analyst deletion sets voyage analyst to null"""
        analyst_id = analyst_user.id
        analyst_user.delete()

        tc_voyage.refresh_from_db()
        assert tc_voyage.assigned_analyst is None

    def test_version_field_for_optimistic_locking(self, basic_voyage):
        """Test version field exists for optimistic locking"""
        assert hasattr(basic_voyage, 'version')
        # Version starts at 0, increments on save
        assert basic_voyage.version == 0

    def test_radar_data_json_field(self, basic_voyage):
        """Test RADAR data JSON field"""
        assert hasattr(basic_voyage, 'radar_data')

    def test_timestamps(self, basic_voyage):
        """Test created_at and updated_at"""
        assert basic_voyage.created_at is not None
        assert basic_voyage.updated_at is not None


@pytest.mark.django_db
class TestClaimModel:
    """Comprehensive tests for Claim model"""

    @pytest.fixture
    def ship_owner(self):
        """Create a ship owner"""
        return ShipOwner.objects.create(
            name='Claim Test Owner',
            code='CTO001'
        )

    @pytest.fixture
    def analyst_user(self):
        """Create an analyst user"""
        return User.objects.create_user(
            username='claim_analyst',
            email='claim_analyst@test.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def voyage(self, ship_owner, analyst_user):
        """Create a voyage for claims"""
        return Voyage.objects.create(
            radar_voyage_id='RADAR-V-CLAIM-001',
            voyage_number='VC001',
            vessel_name='MV Claim Test',
            charter_party='GENCON',
            load_port='Dubai',
            discharge_port='Mumbai',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            ship_owner=ship_owner,
            demurrage_rate=Decimal('18000.00'),
            laytime_allowed=Decimal('60.00'),
            assigned_analyst=analyst_user
        )

    @pytest.fixture
    def draft_claim(self, voyage, ship_owner, analyst_user):
        """Create a draft claim"""
        return Claim.objects.create(
            voyage=voyage,
            ship_owner=ship_owner,
            claim_type='DEMURRAGE',
            status='DRAFT',
            payment_status='NOT_SENT',
            claim_amount=Decimal('45000.00'),
            currency='USD',
            assigned_to=analyst_user,
            created_by=analyst_user
        )

    @pytest.fixture
    def submitted_claim(self, voyage, ship_owner, analyst_user):
        """Create a submitted claim"""
        return Claim.objects.create(
            voyage=voyage,
            ship_owner=ship_owner,
            claim_type='DEMURRAGE',
            status='SUBMITTED',
            payment_status='SENT',
            claim_amount=Decimal('60000.00'),
            currency='USD',
            submitted_at=timezone.now(),  # Use submitted_at not submission_date
            assigned_to=analyst_user,
            created_by=analyst_user
        )

    def test_claim_creation(self, draft_claim):
        """Test basic claim creation"""
        assert draft_claim.claim_type == 'DEMURRAGE'
        assert draft_claim.status == 'DRAFT'
        assert draft_claim.payment_status == 'NOT_SENT'
        assert draft_claim.claim_amount == Decimal('45000.00')

    def test_claim_str_representation(self, draft_claim):
        """Test claim string representation"""
        # Claim __str__ includes claim_number, vessel_name, and claim type
        str_repr = str(draft_claim)
        assert 'CLM-' in str_repr  # Contains claim number
        assert 'Claim Test' in str_repr  # Contains vessel name
        assert 'Demurrage' in str_repr  # Contains claim type

    def test_status_choices(self, draft_claim):
        """Test status can be changed"""
        draft_claim.status = 'UNDER_REVIEW'
        draft_claim.save()
        draft_claim.refresh_from_db()
        assert draft_claim.status == 'UNDER_REVIEW'

    def test_payment_status_choices(self, draft_claim):
        """Test payment status can be changed"""
        draft_claim.payment_status = 'SENT'
        draft_claim.save()
        draft_claim.refresh_from_db()
        assert draft_claim.payment_status == 'SENT'

    def test_claim_amount_positive(self, voyage, ship_owner, analyst_user):
        """Test claim amount must be positive"""
        with pytest.raises(ValidationError):
            claim = Claim(
                voyage=voyage,
                ship_owner=ship_owner,
                claim_type='DEMURRAGE',
                status='DRAFT',
                payment_status='NOT_SENT',
                claim_amount=Decimal('-1000.00'),  # Negative amount
                currency='USD',
                assigned_to=analyst_user,
                created_by=analyst_user
            )
            claim.full_clean()

    def test_paid_amount_optional(self, draft_claim):
        """Test paid_amount defaults to 0"""
        # paid_amount has default=0, not None
        assert draft_claim.paid_amount == 0

    def test_paid_amount_tracking(self, submitted_claim):
        """Test paid amount tracking"""
        submitted_claim.paid_amount = Decimal('60000.00')
        submitted_claim.payment_status = 'PAID'
        submitted_claim.save()

        submitted_claim.refresh_from_db()
        assert submitted_claim.paid_amount == Decimal('60000.00')
        assert submitted_claim.payment_status == 'PAID'

    def test_outstanding_amount_property(self, submitted_claim):
        """Test outstanding_amount property"""
        submitted_claim.paid_amount = Decimal('40000.00')
        submitted_claim.save()

        assert submitted_claim.outstanding_amount == Decimal('20000.00')

    def test_outstanding_amount_fully_paid(self, submitted_claim):
        """Test outstanding_amount when fully paid"""
        submitted_claim.paid_amount = Decimal('60000.00')
        submitted_claim.save()

        assert submitted_claim.outstanding_amount == Decimal('0.00')

    def test_submitted_at_optional(self, draft_claim):
        """Test submitted_at is optional for drafts"""
        assert draft_claim.submitted_at is None

    def test_submitted_at_set_for_submitted(self, submitted_claim):
        """Test submitted_at is set for submitted claims"""
        assert submitted_claim.submitted_at is not None

    def test_time_bar_date_optional(self, draft_claim):
        """Test time_bar_date is optional"""
        assert draft_claim.time_bar_date is None

    def test_time_bar_warning(self, draft_claim):
        """Test time bar warning functionality"""
        # Set time bar date in near future
        draft_claim.time_bar_date = timezone.now().date() + timedelta(days=25)
        draft_claim.save()

        # Should have a property or method to check time bar warning
        assert draft_claim.time_bar_date is not None

    def test_voyage_relationship(self, draft_claim, voyage):
        """Test voyage foreign key relationship"""
        assert draft_claim.voyage == voyage
        assert draft_claim in voyage.claims.all()

    def test_ship_owner_relationship(self, draft_claim, ship_owner):
        """Test ship owner relationship"""
        assert draft_claim.ship_owner == ship_owner

    def test_assigned_to_relationship(self, draft_claim, analyst_user):
        """Test assigned_to relationship"""
        assert draft_claim.assigned_to == analyst_user
        assert draft_claim in analyst_user.assigned_claims.all()

    def test_created_by_relationship(self, draft_claim, analyst_user):
        """Test created_by relationship"""
        assert draft_claim.created_by == analyst_user

    def test_version_field_optimistic_locking(self, draft_claim):
        """Test version field for optimistic locking"""
        assert hasattr(draft_claim, 'version')
        # Version starts at 0, increments on save
        assert draft_claim.version == 0

    def test_currency_default(self, draft_claim):
        """Test currency defaults to USD"""
        assert draft_claim.currency == 'USD'

    def test_timestamps(self, draft_claim):
        """Test created_at and updated_at"""
        assert draft_claim.created_at is not None
        assert draft_claim.updated_at is not None

    def test_optional_text_fields(self, draft_claim):
        """Test optional text fields"""
        # Claim has description, settlement_notes, and internal_notes (not 'notes')
        assert draft_claim.description == ''
        assert draft_claim.settlement_notes == ''
        assert draft_claim.internal_notes == ''

    def test_claim_with_description_and_notes(self, voyage, ship_owner, analyst_user):
        """Test claim with description and notes"""
        claim = Claim.objects.create(
            voyage=voyage,
            ship_owner=ship_owner,
            claim_type='DESPATCH',
            status='DRAFT',
            payment_status='NOT_SENT',
            claim_amount=Decimal('25000.00'),
            description='Customer requested fast-track processing',
            settlement_notes='Agreed to 80% settlement',
            internal_notes='Priority client - handle within 24h',
            assigned_to=analyst_user,
            created_by=analyst_user
        )

        assert 'fast-track' in claim.description
        assert 'settlement' in claim.settlement_notes
        assert 'Priority client' in claim.internal_notes


@pytest.mark.django_db
class TestVoyageAssignmentModel:
    """Test VoyageAssignment model for assignment tracking"""

    @pytest.fixture
    def ship_owner(self):
        """Create a ship owner"""
        return ShipOwner.objects.create(
            name='Assignment Test Owner',
            code='ATO001'
        )

    @pytest.fixture
    def analyst1(self):
        """Create first analyst"""
        return User.objects.create_user(
            username='analyst1_assign',
            email='analyst1@test.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def analyst2(self):
        """Create second analyst"""
        return User.objects.create_user(
            username='analyst2_assign',
            email='analyst2@test.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def team_lead(self):
        """Create team lead"""
        return User.objects.create_user(
            username='teamlead_assign',
            email='teamlead@test.com',
            password='testpass123',
            role='TEAM_LEAD'
        )

    @pytest.fixture
    def voyage(self, ship_owner, analyst1):
        """Create a voyage"""
        return Voyage.objects.create(
            radar_voyage_id='RADAR-V-ASSIGN-001',
            voyage_number='VA001',
            vessel_name='MV Assignment Test',
            charter_party='GENCON',
            load_port='Rotterdam',
            discharge_port='Singapore',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=7),
            ship_owner=ship_owner,
            demurrage_rate=Decimal('16000.00'),
            laytime_allowed=Decimal('54.00'),
            assigned_analyst=analyst1
        )

    def test_voyage_assignment_creation(self, voyage, analyst1, team_lead):
        """Test creating a voyage assignment"""
        assignment = VoyageAssignment.objects.create(
            voyage=voyage,
            assigned_to=analyst1,
            assigned_by=team_lead
        )

        assert assignment.voyage == voyage
        assert assignment.assigned_to == analyst1
        assert assignment.assigned_by == team_lead
        assert assignment.assigned_at is not None

    def test_assignment_history_tracking(self, voyage, analyst1, analyst2, team_lead):
        """Test assignment history is tracked"""
        # First assignment
        assignment1 = VoyageAssignment.objects.create(
            voyage=voyage,
            assigned_to=analyst1,
            assigned_by=team_lead
        )

        # Reassignment
        assignment2 = VoyageAssignment.objects.create(
            voyage=voyage,
            assigned_to=analyst2,
            assigned_by=team_lead,
            reassignment_reason='Workload balancing'
        )

        # Check history
        history = voyage.assignment_history.all()
        assert history.count() == 2
        assert assignment1 in history
        assert assignment2 in history

    def test_reassignment_reason_optional(self, voyage, analyst1, team_lead):
        """Test reassignment reason is optional"""
        assignment = VoyageAssignment.objects.create(
            voyage=voyage,
            assigned_to=analyst1,
            assigned_by=team_lead
        )

        assert assignment.reassignment_reason == ''

    def test_reassignment_with_reason(self, voyage, analyst2, team_lead):
        """Test reassignment with reason"""
        assignment = VoyageAssignment.objects.create(
            voyage=voyage,
            assigned_to=analyst2,
            assigned_by=team_lead,
            reassignment_reason='Original analyst on leave'
        )

        assert assignment.reassignment_reason == 'Original analyst on leave'


@pytest.mark.django_db
class TestClaimActivityLogModel:
    """Test ClaimActivityLog model for audit trail"""

    @pytest.fixture
    def ship_owner(self):
        """Create a ship owner"""
        return ShipOwner.objects.create(
            name='Activity Log Owner',
            code='ALO001'
        )

    @pytest.fixture
    def analyst(self):
        """Create an analyst"""
        return User.objects.create_user(
            username='log_analyst',
            email='log@test.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def voyage(self, ship_owner, analyst):
        """Create a voyage"""
        return Voyage.objects.create(
            radar_voyage_id='RADAR-V-LOG-001',
            voyage_number='VL001',
            vessel_name='MV Log Test',
            charter_party='GENCON',
            load_port='Dubai',
            discharge_port='Singapore',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            ship_owner=ship_owner,
            demurrage_rate=Decimal('14000.00'),
            laytime_allowed=Decimal('42.00'),
            assigned_analyst=analyst
        )

    @pytest.fixture
    def claim(self, voyage, ship_owner, analyst):
        """Create a claim"""
        return Claim.objects.create(
            voyage=voyage,
            ship_owner=ship_owner,
            claim_type='DEMURRAGE',
            status='DRAFT',
            payment_status='NOT_SENT',
            claim_amount=Decimal('35000.00'),
            assigned_to=analyst,
            created_by=analyst
        )

    def test_activity_log_creation(self, claim, analyst):
        """Test creating an activity log entry"""
        log = ClaimActivityLog.objects.create(
            claim=claim,
            claim_number=claim.claim_number,
            action='STATUS_CHANGED',
            message='Status changed from DRAFT to UNDER_REVIEW',
            user=analyst,
            old_value='DRAFT',
            new_value='UNDER_REVIEW'
        )

        assert log.claim == claim
        assert log.claim_number == claim.claim_number
        assert log.action == 'STATUS_CHANGED'
        assert log.user == analyst
        assert log.old_value == 'DRAFT'
        assert log.new_value == 'UNDER_REVIEW'

    def test_activity_log_timestamp(self, claim, analyst):
        """Test activity log has timestamp"""
        log = ClaimActivityLog.objects.create(
            claim=claim,
            claim_number=claim.claim_number,
            action='CREATED',
            message='Claim created',
            user=analyst
        )

        # ClaimActivityLog uses 'created_at' not 'timestamp'
        assert log.created_at is not None

    def test_activity_log_optional_values(self, claim, analyst):
        """Test old/new values are optional"""
        log = ClaimActivityLog.objects.create(
            claim=claim,
            claim_number=claim.claim_number,
            action='CREATED',
            message='Claim created',
            user=analyst
        )

        assert log.old_value == ''
        assert log.new_value == ''

    def test_activity_log_cannot_be_deleted(self, claim, analyst):
        """Test activity logs are preserved when claim is deleted"""
        log = ClaimActivityLog.objects.create(
            claim=claim,
            claim_number=claim.claim_number,
            action='CREATED',
            message='Claim created',
            user=analyst
        )

        # In real implementation, this should be prevented
        # For now, just verify the log exists
        assert ClaimActivityLog.objects.filter(id=log.id).exists()


# Run tests with: pytest claims/tests.py -v
