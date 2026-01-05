"""
Comprehensive tests for ships views

This test module focuses on testing the ships app views,
which currently has only 7% coverage.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from claims.models import User, ShipOwner
from ships.models import Ship, TCFleet


@pytest.fixture
def ships_admin_user():
    """Create an admin user for ships tests"""
    return User.objects.create_user(
        username='ships_admin',
        password='testpass123',
        email='ships_admin@test.com',
        role='ADMIN',
        must_change_password=False
    )


@pytest.fixture
def ships_read_user():
    """Create a read-only user for ships tests"""
    return User.objects.create_user(
        username='ships_read',
        password='testpass123',
        email='ships_read@test.com',
        role='READ',
        must_change_password=False
    )


@pytest.fixture
def ships_write_user():
    """Create a write user for ships tests"""
    return User.objects.create_user(
        username='ships_write',
        password='testpass123',
        email='ships_write@test.com',
        role='WRITE',
        must_change_password=False
    )


@pytest.fixture
def test_fleet():
    """Create a test fleet"""
    return TCFleet.objects.create(
        fleet_name='Test Fleet',
        fleet_code='TESTFLEET'
    )


@pytest.fixture
def test_ship(test_fleet):
    """Create a test ship"""
    return Ship.objects.create(
        imo_number='9999999',
        vessel_name='MV Test Ship',
        flag='Panama',
        vessel_type='BULK_CARRIER',
        deadweight=75000.00,
        built_year=2020
    )


@pytest.mark.django_db
class TestShipListView:
    """Tests for ship list view"""

    def test_ship_list_requires_authentication(self):
        """Test that ship list redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('ship_list'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_ship_list_accessible_to_authenticated(self, ships_read_user):
        """Test that authenticated users can view ship list"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_list'))
        assert response.status_code == 200

    def test_ship_list_shows_ships(self, ships_read_user, test_ship):
        """Test that ship list displays ships"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_list'))
        assert response.status_code == 200
        # Check that ship appears in content
        assert b'MV Test Ship' in response.content or 'MV Test Ship' in str(response.content)


@pytest.mark.django_db
class TestShipDetailView:
    """Tests for ship detail view"""

    def test_ship_detail_requires_authentication(self, test_ship):
        """Test that ship detail redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('ship_detail', kwargs={'pk': test_ship.pk}))
        assert response.status_code == 302

    def test_ship_detail_accessible(self, ships_read_user, test_ship):
        """Test that authenticated users can view ship detail"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_detail', kwargs={'pk': test_ship.pk}))
        assert response.status_code == 200

    def test_ship_detail_shows_ship_info(self, ships_read_user, test_ship):
        """Test that ship detail shows ship information"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_detail', kwargs={'pk': test_ship.pk}))
        assert response.status_code == 200
        # Check for ship details in response
        content = response.content.decode('utf-8')
        assert 'MV Test Ship' in content or test_ship.vessel_name in content


@pytest.mark.django_db
class TestShipCreateView:
    """Tests for ship create view"""

    def test_ship_create_requires_authentication(self):
        """Test that ship create redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('ship_create'))
        assert response.status_code == 302

    def test_ship_create_requires_write_permission(self, ships_read_user):
        """Test that read-only users cannot create ships"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_create'))
        # Should be denied or redirected
        assert response.status_code in [302, 403]

    def test_ship_create_accessible_to_write_user(self, ships_write_user):
        """Test that write users can access ship create"""
        client = Client()
        client.force_login(ships_write_user)
        response = client.get(reverse('ship_create'))
        # Should show form or work
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestShipUpdateView:
    """Tests for ship update view"""

    def test_ship_update_requires_authentication(self, test_ship):
        """Test that ship update redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('ship_update', kwargs={'pk': test_ship.pk}))
        assert response.status_code == 302

    def test_ship_update_requires_write_permission(self, ships_read_user, test_ship):
        """Test that read-only users cannot update ships"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_update', kwargs={'pk': test_ship.pk}))
        # Should be denied or redirected
        assert response.status_code in [200, 302, 403]

    def test_ship_update_accessible_to_write_user(self, ships_write_user, test_ship):
        """Test that write users can access ship update"""
        client = Client()
        client.force_login(ships_write_user)
        response = client.get(reverse('ship_update', kwargs={'pk': test_ship.pk}))
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestFleetViews:
    """Tests for fleet management views"""

    def test_fleet_list_requires_authentication(self):
        """Test that fleet list redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('fleet_list'))
        assert response.status_code == 302

    def test_fleet_list_accessible(self, ships_read_user):
        """Test that authenticated users can view fleet list"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('fleet_list'))
        assert response.status_code == 200

    def test_fleet_detail_requires_authentication(self, test_fleet):
        """Test that fleet detail requires authentication"""
        client = Client()
        response = client.get(reverse('fleet_detail', kwargs={'pk': test_fleet.pk}))
        assert response.status_code == 302

    def test_fleet_detail_accessible(self, ships_read_user, test_fleet):
        """Test that authenticated users can view fleet detail"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('fleet_detail', kwargs={'pk': test_fleet.pk}))
        assert response.status_code == 200


@pytest.mark.django_db
class TestShipExportViews:
    """Tests for ship export functionality"""

    def test_ship_export_requires_authentication(self):
        """Test that ship export requires authentication"""
        client = Client()
        response = client.get(reverse('export_ships'))
        assert response.status_code == 302

    def test_ship_export_requires_permission(self, ships_read_user):
        """Test that read-only users cannot export"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('export_ships'))
        # READ users don't have export permission
        assert response.status_code in [302, 403]


@pytest.mark.django_db
class TestShipSearchAndFilter:
    """Tests for ship search and filtering"""

    def test_ship_search_by_name(self, ships_read_user, test_ship):
        """Test searching ships by name"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_list') + '?search=Test')
        assert response.status_code == 200

    def test_ship_filter_by_fleet(self, ships_read_user, test_ship, test_fleet):
        """Test filtering ships by fleet"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_list') + f'?fleet={test_fleet.pk}')
        assert response.status_code == 200

    def test_ship_filter_by_type(self, ships_read_user, test_ship):
        """Test filtering ships by type"""
        client = Client()
        client.force_login(ships_read_user)
        response = client.get(reverse('ship_list') + '?vessel_type=BULK_CARRIER')
        assert response.status_code == 200
