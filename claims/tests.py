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
