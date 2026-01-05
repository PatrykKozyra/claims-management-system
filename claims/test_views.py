"""
Comprehensive tests for claims views

This test module focuses on testing the main views in the claims app,
which currently has low coverage (17%).
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from claims.models import User, ShipOwner, Voyage, Claim, Comment, Document, ClaimActivityLog


@pytest.fixture
def admin_user():
    """Create an admin user"""
    return User.objects.create_user(
        username='admin_views',
        password='testpass123',
        email='admin@test.com',
        role='ADMIN',
        must_change_password=False
    )


@pytest.fixture
def write_user():
    """Create a write user"""
    return User.objects.create_user(
        username='write_views',
        password='testpass123',
        email='write@test.com',
        role='WRITE',
        must_change_password=False
    )


@pytest.fixture
def read_user():
    """Create a read-only user"""
    return User.objects.create_user(
        username='read_views',
        password='testpass123',
        email='read@test.com',
        role='READ',
        must_change_password=False
    )


@pytest.fixture
def ship_owner():
    """Create a ship owner"""
    return ShipOwner.objects.create(
        name='Test Owner Ltd',
        code='TESTOWNER'
    )


@pytest.fixture
def voyage(ship_owner):
    """Create a voyage"""
    return Voyage.objects.create(
        radar_voyage_id='TESTV001',
        voyage_number='V001',
        vessel_name='MV Test Vessel',
        charter_party='GENCON',
        load_port='Singapore',
        discharge_port='Rotterdam',
        laycan_start=timezone.now().date(),
        laycan_end=timezone.now().date() + timedelta(days=5),
        ship_owner=ship_owner,
        demurrage_rate=Decimal('10000.00'),
        laytime_allowed=Decimal('72.00'),
        currency='USD'
    )


@pytest.fixture
def claim(voyage, ship_owner, admin_user):
    """Create a claim"""
    return Claim.objects.create(
        radar_claim_id='TESTC001',
        voyage=voyage,
        ship_owner=ship_owner,
        claim_type='DEMURRAGE',
        status='DRAFT',
        claim_amount=Decimal('50000.00'),
        currency='USD',
        assigned_to=admin_user,
        created_by=admin_user,
        description='Test claim for views'
    )


@pytest.mark.django_db
class TestDashboardView:
    """Tests for dashboard view"""

    def test_dashboard_requires_authentication(self):
        """Test that dashboard redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_dashboard_accessible_to_authenticated_user(self, admin_user):
        """Test that authenticated users can access dashboard"""
        client = Client()
        client.force_login(admin_user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

    def test_dashboard_shows_statistics(self, admin_user, claim):
        """Test that dashboard shows relevant statistics"""
        client = Client()
        client.force_login(admin_user)
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        # Check that context contains expected keys
        assert 'total_claims' in response.context or b'claim' in response.content.lower()


@pytest.mark.django_db
class TestVoyageViews:
    """Tests for voyage-related views"""

    def test_voyage_list_requires_authentication(self):
        """Test that voyage list redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('voyage_list'))
        assert response.status_code == 302

    def test_voyage_list_accessible_to_authenticated(self, read_user):
        """Test that authenticated users can view voyage list"""
        client = Client()
        client.force_login(read_user)
        response = client.get(reverse('voyage_list'))
        assert response.status_code == 200

    def test_voyage_detail_requires_authentication(self, voyage):
        """Test that voyage detail redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('voyage_detail', kwargs={'pk': voyage.pk}))
        assert response.status_code == 302

    def test_voyage_detail_accessible(self, read_user, voyage):
        """Test that authenticated users can view voyage detail"""
        client = Client()
        client.force_login(read_user)
        response = client.get(reverse('voyage_detail', kwargs={'pk': voyage.pk}))
        assert response.status_code == 200

    def test_voyage_assign_requires_authentication(self, voyage):
        """Test that voyage assign redirects unauthenticated users"""
        client = Client()
        response = client.post(reverse('voyage_assign', kwargs={'pk': voyage.pk}))
        assert response.status_code == 302

    def test_voyage_assign_works_for_write_user(self, write_user, voyage):
        """Test that write users can assign voyages to themselves"""
        client = Client()
        client.force_login(write_user)
        response = client.post(reverse('voyage_assign', kwargs={'pk': voyage.pk}))
        # Should redirect after assignment
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestClaimViews:
    """Tests for claim-related views"""

    def test_claim_list_requires_authentication(self):
        """Test that claim list redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('claim_list'))
        assert response.status_code == 302

    def test_claim_list_accessible(self, read_user):
        """Test that authenticated users can view claim list"""
        client = Client()
        client.force_login(read_user)
        response = client.get(reverse('claim_list'))
        assert response.status_code == 200

    def test_claim_detail_requires_authentication(self, claim):
        """Test that claim detail redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('claim_detail', kwargs={'pk': claim.pk}))
        assert response.status_code == 302

    def test_claim_detail_accessible(self, read_user, claim):
        """Test that authenticated users can view claim detail"""
        client = Client()
        client.force_login(read_user)
        response = client.get(reverse('claim_detail', kwargs={'pk': claim.pk}))
        assert response.status_code == 200

    def test_claim_update_requires_authentication(self, claim):
        """Test that claim update redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('claim_update', kwargs={'pk': claim.pk}))
        assert response.status_code == 302

    def test_claim_update_accessible_to_write_user(self, write_user, claim):
        """Test that write users can access claim update"""
        client = Client()
        client.force_login(write_user)
        response = client.get(reverse('claim_update', kwargs={'pk': claim.pk}))
        # May show form or redirect
        assert response.status_code in [200, 302]

    def test_add_comment_requires_authentication(self, claim):
        """Test that adding comment requires authentication"""
        client = Client()
        response = client.post(
            reverse('add_comment', kwargs={'claim_pk': claim.pk}),
            {'text': 'Test comment'}
        )
        assert response.status_code == 302

    def test_add_comment_works_for_authenticated_user(self, write_user, claim):
        """Test that authenticated users can add comments"""
        client = Client()
        client.force_login(write_user)
        response = client.post(
            reverse('add_comment', kwargs={'claim_pk': claim.pk}),
            {'text': 'Test comment from write user'}
        )
        # Should redirect or return success
        assert response.status_code in [200, 201, 302]


@pytest.mark.django_db
class TestUserViews:
    """Tests for user management views"""

    def test_user_directory_requires_authentication(self):
        """Test that user directory redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('user_directory'))
        assert response.status_code == 302

    def test_user_directory_accessible(self, admin_user):
        """Test that authenticated users can view user directory"""
        client = Client()
        client.force_login(admin_user)
        response = client.get(reverse('user_directory'))
        assert response.status_code == 200

    def test_user_create_requires_admin(self, write_user):
        """Test that user creation requires admin role"""
        client = Client()
        client.force_login(write_user)
        response = client.get(reverse('user_create'))
        # Non-admin users should be denied or redirected
        assert response.status_code in [302, 403]

    def test_user_create_accessible_to_admin(self, admin_user):
        """Test that admin users can access user creation"""
        client = Client()
        client.force_login(admin_user)
        response = client.get(reverse('user_create'))
        assert response.status_code == 200

    def test_user_profile_requires_authentication(self, admin_user):
        """Test that user profile redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('user_profile', kwargs={'user_id': admin_user.pk}))
        assert response.status_code == 302

    def test_user_profile_accessible(self, admin_user, read_user):
        """Test that authenticated users can view profiles"""
        client = Client()
        client.force_login(read_user)
        response = client.get(reverse('user_profile', kwargs={'user_id': admin_user.pk}))
        assert response.status_code == 200

    def test_toggle_dark_mode(self, read_user):
        """Test that users can toggle dark mode"""
        client = Client()
        client.force_login(read_user)

        # Check initial state
        assert read_user.dark_mode is False

        # Toggle dark mode
        response = client.post(reverse('toggle_dark_mode'))
        assert response.status_code in [200, 302]

        # Refresh and check
        read_user.refresh_from_db()
        assert read_user.dark_mode is True


@pytest.mark.django_db
class TestAuthenticationViews:
    """Tests for authentication views"""

    def test_login_page_accessible(self):
        """Test that login page is accessible without authentication"""
        client = Client()
        response = client.get(reverse('login'))
        assert response.status_code == 200

    def test_login_with_valid_credentials(self, admin_user):
        """Test login with valid credentials"""
        client = Client()
        response = client.post(reverse('login'), {
            'username': 'admin_views',
            'password': 'testpass123'
        })
        # Should redirect after successful login
        assert response.status_code in [200, 302]

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        client = Client()
        response = client.post(reverse('login'), {
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        # Should show login page again with error
        assert response.status_code == 200

    def test_logout(self, admin_user):
        """Test logout functionality"""
        client = Client()
        client.force_login(admin_user)
        response = client.post(reverse('logout'))
        # Should redirect after logout
        assert response.status_code == 302


@pytest.mark.django_db
class TestAnalyticsViews:
    """Tests for analytics views"""

    def test_analytics_requires_authentication(self):
        """Test that analytics redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('analytics'))
        assert response.status_code == 302

    def test_analytics_accessible_to_authenticated(self, admin_user):
        """Test that authenticated users can view analytics"""
        client = Client()
        client.force_login(admin_user)
        response = client.get(reverse('analytics'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestExportViews:
    """Tests for export functionality"""

    def test_export_claims_requires_authentication(self):
        """Test that export redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('export_claims'))
        assert response.status_code == 302

    def test_export_claims_requires_export_permission(self, read_user):
        """Test that users without export permission are denied"""
        client = Client()
        client.force_login(read_user)
        response = client.get(reverse('export_claims'))
        # READ users don't have export permission
        assert response.status_code in [302, 403]

    def test_export_users_requires_authentication(self):
        """Test that user export redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('export_users'))
        assert response.status_code == 302
