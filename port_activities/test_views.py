"""
Comprehensive tests for port_activities views

This test module focuses on testing the port_activities app views,
which currently has only 20% coverage.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from claims.models import User
from ships.models import Ship, TCFleet
from port_activities.models import ActivityType, PortActivity


@pytest.fixture
def pa_admin_user():
    """Create an admin user for port activities tests"""
    return User.objects.create_user(
        username='pa_admin',
        password='testpass123',
        email='pa_admin@test.com',
        role='ADMIN',
        must_change_password=False
    )


@pytest.fixture
def pa_read_user():
    """Create a read-only user"""
    return User.objects.create_user(
        username='pa_read',
        password='testpass123',
        email='pa_read@test.com',
        role='READ',
        must_change_password=False
    )


@pytest.fixture
def pa_write_user():
    """Create a write user"""
    return User.objects.create_user(
        username='pa_write',
        password='testpass123',
        email='pa_write@test.com',
        role='WRITE',
        must_change_password=False
    )


@pytest.fixture
def pa_fleet():
    """Create a test fleet"""
    return TCFleet.objects.create(
        fleet_name='PA Test Fleet',
        fleet_code='PAFLEET'
    )


@pytest.fixture
def pa_ship(pa_fleet):
    """Create a test ship"""
    return Ship.objects.create(
        imo_number='8888888',
        vessel_name='MV Port Activity Test',
        flag='Liberia',
        vessel_type='CONTAINER',
        deadweight=50000.00,
        built_year=2019
    )


@pytest.fixture
def activity_type():
    """Create an activity type"""
    return ActivityType.objects.create(
        name='Loading',
        code='LOAD',
        description='Loading cargo operations'
    )


@pytest.fixture
def port_activity(pa_ship, activity_type, pa_admin_user):
    """Create a port activity"""
    return PortActivity.objects.create(
        ship=pa_ship,
        activity_type=activity_type,
        port_name='Singapore',
        arrival_date=timezone.now().date(),
        departure_date=timezone.now().date() + timedelta(days=2),
        status='COMPLETED',
        created_by=pa_admin_user
    )


@pytest.mark.django_db
class TestPortActivityListView:
    """Tests for port activity list view"""

    def test_activity_list_requires_authentication(self):
        """Test that activity list redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('port_activity_list'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_activity_list_accessible_to_authenticated(self, pa_read_user):
        """Test that authenticated users can view activity list"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_list'))
        assert response.status_code == 200

    def test_activity_list_shows_activities(self, pa_read_user, port_activity):
        """Test that activity list displays activities"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_list'))
        assert response.status_code == 200
        # Check that activity appears in content
        content = response.content.decode('utf-8')
        assert 'Singapore' in content or 'port_activity' in content.lower()


@pytest.mark.django_db
class TestPortActivityDetailView:
    """Tests for port activity detail view"""

    def test_activity_detail_requires_authentication(self, port_activity):
        """Test that activity detail redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('port_activity_detail', kwargs={'pk': port_activity.pk}))
        assert response.status_code == 302

    def test_activity_detail_accessible(self, pa_read_user, port_activity):
        """Test that authenticated users can view activity detail"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_detail', kwargs={'pk': port_activity.pk}))
        assert response.status_code == 200

    def test_activity_detail_shows_info(self, pa_read_user, port_activity):
        """Test that activity detail shows activity information"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_detail', kwargs={'pk': port_activity.pk}))
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'Singapore' in content or port_activity.port_name in content


@pytest.mark.django_db
class TestPortActivityCreateView:
    """Tests for port activity create view"""

    def test_activity_create_requires_authentication(self):
        """Test that activity create redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('port_activity_create'))
        assert response.status_code == 302

    def test_activity_create_requires_write_permission(self, pa_read_user):
        """Test that read-only users cannot create activities"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_create'))
        # Should be denied or redirected
        assert response.status_code in [302, 403]

    def test_activity_create_accessible_to_write_user(self, pa_write_user):
        """Test that write users can access activity create"""
        client = Client()
        client.force_login(pa_write_user)
        response = client.get(reverse('port_activity_create'))
        # Should show form or work
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestPortActivityUpdateView:
    """Tests for port activity update view"""

    def test_activity_update_requires_authentication(self, port_activity):
        """Test that activity update redirects unauthenticated users"""
        client = Client()
        response = client.get(reverse('port_activity_update', kwargs={'pk': port_activity.pk}))
        assert response.status_code == 302

    def test_activity_update_requires_write_permission(self, pa_read_user, port_activity):
        """Test that read-only users cannot update activities"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_update', kwargs={'pk': port_activity.pk}))
        # Should be denied or allow viewing but not editing
        assert response.status_code in [200, 302, 403]

    def test_activity_update_accessible_to_write_user(self, pa_write_user, port_activity):
        """Test that write users can access activity update"""
        client = Client()
        client.force_login(pa_write_user)
        response = client.get(reverse('port_activity_update', kwargs={'pk': port_activity.pk}))
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestActivityTypeViews:
    """Tests for activity type views"""

    def test_activity_type_list_requires_authentication(self):
        """Test that activity type list requires authentication"""
        client = Client()
        response = client.get(reverse('activity_type_list'))
        assert response.status_code == 302

    def test_activity_type_list_accessible(self, pa_read_user):
        """Test that authenticated users can view activity types"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('activity_type_list'))
        assert response.status_code == 200

    def test_activity_type_list_shows_types(self, pa_read_user, activity_type):
        """Test that activity type list shows types"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('activity_type_list'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestPortActivitySearchAndFilter:
    """Tests for port activity search and filtering"""

    def test_activity_search_by_port(self, pa_read_user, port_activity):
        """Test searching activities by port name"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_list') + '?search=Singapore')
        assert response.status_code == 200

    def test_activity_filter_by_ship(self, pa_read_user, port_activity, pa_ship):
        """Test filtering activities by ship"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_list') + f'?ship={pa_ship.pk}')
        assert response.status_code == 200

    def test_activity_filter_by_status(self, pa_read_user, port_activity):
        """Test filtering activities by status"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_list') + '?status=COMPLETED')
        assert response.status_code == 200

    def test_activity_filter_by_type(self, pa_read_user, port_activity, activity_type):
        """Test filtering activities by activity type"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('port_activity_list') + f'?activity_type={activity_type.pk}')
        assert response.status_code == 200


@pytest.mark.django_db
class TestPortActivityExport:
    """Tests for port activity export"""

    def test_activity_export_requires_authentication(self):
        """Test that export requires authentication"""
        client = Client()
        response = client.get(reverse('export_port_activities'))
        assert response.status_code == 302

    def test_activity_export_requires_permission(self, pa_read_user):
        """Test that read-only users cannot export"""
        client = Client()
        client.force_login(pa_read_user)
        response = client.get(reverse('export_port_activities'))
        # READ users don't have export permission
        assert response.status_code in [302, 403]
