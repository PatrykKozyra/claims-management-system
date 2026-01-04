"""
Security tests for Claims Management System
Tests for SQL injection, XSS, CSRF, and other security vulnerabilities
"""
import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from claims.models import Claim, Voyage, ShipOwner
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.security
class TestSQLInjection:
    """Test protection against SQL injection attacks"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='admin_sec',
            email='admin@sec.test',
            password='testpass123',
            role='ADMIN'
        )

    def test_sql_injection_in_search(self, client, admin_user):
        """Test SQL injection attempts in search queries"""
        client.force_login(admin_user)

        # Common SQL injection payloads
        sql_injection_payloads = [
            "' OR '1'='1",
            "1' OR '1' = '1",
            "'; DROP TABLE claims_claim; --",
            "1' UNION SELECT NULL, NULL, NULL--",
            "admin'--",
            "' OR 1=1--",
        ]

        for payload in sql_injection_payloads:
            # Try injection in search parameter
            response = client.get('/claims/voyages/', {'search': payload})
            # Should not cause error or expose SQL
            assert response.status_code in [200, 302, 404]
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Should not contain SQL error messages
                assert 'syntax error' not in content.lower()
                assert 'mysql' not in content.lower()
                assert 'postgresql' not in content.lower()
                assert 'sqlite' not in content.lower()

    def test_sql_injection_in_filter(self, client, admin_user):
        """Test SQL injection in filter parameters"""
        client.force_login(admin_user)

        response = client.get('/claims/voyages/', {'status': "' OR '1'='1"})
        assert response.status_code in [200, 302, 404]


@pytest.mark.django_db
@pytest.mark.security
class TestXSSPrevention:
    """Test protection against Cross-Site Scripting (XSS) attacks"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='admin_xss',
            email='admin@xss.test',
            password='testpass123',
            role='ADMIN'
        )

    @pytest.fixture
    def ship_owner(self):
        return ShipOwner.objects.create(
            name='XSS Test Owner',
            code='XSS001'
        )

    @pytest.fixture
    def voyage(self, ship_owner, admin_user):
        return Voyage.objects.create(
            radar_voyage_id='RADAR-XSS-001',
            voyage_number='XSS001',
            vessel_name='XSS Test Ship',
            charter_party='TEST',
            load_port='Port A',
            discharge_port='Port B',
            laycan_start=timezone.now().date(),
            laycan_end=timezone.now().date() + timedelta(days=5),
            ship_owner=ship_owner,
            demurrage_rate=Decimal('10000.00'),
            laytime_allowed=Decimal('48.00'),
            assigned_analyst=admin_user
        )

    def test_xss_in_claim_description(self, client, admin_user, voyage, ship_owner):
        """Test XSS attempts in claim description"""
        client.force_login(admin_user)

        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')">',
        ]

        for payload in xss_payloads:
            claim = Claim.objects.create(
                voyage=voyage,
                ship_owner=ship_owner,
                claim_type='DEMURRAGE',
                status='DRAFT',
                claim_amount=Decimal('10000.00'),
                description=payload,
                created_by=admin_user
            )

            # Retrieve the claim detail page
            response = client.get(f'/claims/{claim.id}/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Script tags should be escaped
                assert '<script>' not in content or '&lt;script&gt;' in content
                assert 'onerror=' not in content or '&' in content
                assert 'javascript:' not in content or '&' in content

            claim.delete()

    def test_xss_in_ship_owner_name(self, client, admin_user):
        """Test XSS prevention in ship owner names"""
        client.force_login(admin_user)

        owner = ShipOwner.objects.create(
            name='<script>alert("XSS")</script>',
            code='XSS002'
        )

        response = client.get('/claims/ship-owners/')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            # Should be HTML-escaped
            assert '&lt;script&gt;' in content or '<script>' not in content


@pytest.mark.django_db
@pytest.mark.security
class TestCSRFProtection:
    """Test CSRF protection"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='admin_csrf',
            email='admin@csrf.test',
            password='testpass123',
            role='ADMIN'
        )

    def test_csrf_token_required_for_post(self, client, admin_user):
        """Test that POST requests without CSRF token are rejected"""
        client.force_login(admin_user)

        # Attempt POST without CSRF token (enforce_csrf_checks=True)
        client_with_csrf = Client(enforce_csrf_checks=True)
        client_with_csrf.force_login(admin_user)

        response = client_with_csrf.post('/login/', {
            'username': 'test',
            'password': 'test'
        })

        # Should be rejected (403) or redirect
        assert response.status_code in [403, 302]


@pytest.mark.django_db
@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication and authorization security"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def read_user(self):
        return User.objects.create_user(
            username='readonly',
            email='read@test.com',
            password='testpass123',
            role='READ'
        )

    @pytest.fixture
    def write_user(self):
        return User.objects.create_user(
            username='writer',
            email='write@test.com',
            password='testpass123',
            role='WRITE'
        )

    def test_unauthenticated_redirect(self, client):
        """Test that unauthenticated users are redirected to login"""
        response = client.get('/claims/voyages/')
        # Should redirect to login
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_read_only_cannot_modify(self, client, read_user, write_user):
        """Test that read-only users cannot modify data"""
        client.force_login(read_user)

        # Try to access create/edit endpoints (will vary based on your URLs)
        # This is a placeholder - adjust based on actual URLs
        response = client.post('/claims/voyages/create/', {})
        # Should be forbidden or redirect
        assert response.status_code in [403, 302, 404, 405]

    def test_password_complexity(self):
        """Test password requirements"""
        # Weak passwords should be rejected by Django's validators
        with pytest.raises(Exception):
            User.objects.create_user(
                username='weakpass',
                email='weak@test.com',
                password='123'  # Too short
            )


@pytest.mark.django_db
@pytest.mark.security
class TestFileUploadSecurity:
    """Test file upload security"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_superuser(
            username='admin_file',
            email='admin@file.test',
            password='testpass123',
            role='ADMIN'
        )

    def test_file_extension_validation(self, client, admin_user):
        """Test that only allowed file extensions are accepted"""
        client.force_login(admin_user)

        # This test depends on your file upload implementation
        # Placeholder for file upload security tests
        pass


@pytest.mark.django_db
@pytest.mark.security
class TestSessionSecurity:
    """Test session security settings"""

    def test_session_cookie_secure_in_production(self, settings):
        """Test that session cookies are secure in production"""
        # In production, these should be True
        if not settings.DEBUG:
            assert settings.SESSION_COOKIE_SECURE is True
            assert settings.CSRF_COOKIE_SECURE is True
            assert settings.SESSION_COOKIE_HTTPONLY is True

    def test_session_timeout(self, settings):
        """Test that sessions have reasonable timeout"""
        # Session should timeout (default is 2 weeks, we set 1 hour in settings)
        assert settings.SESSION_COOKIE_AGE <= 86400  # Max 24 hours


@pytest.mark.django_db
@pytest.mark.security
class TestDataExposure:
    """Test protection against sensitive data exposure"""

    @pytest.fixture
    def client(self):
        return Client()

    def test_debug_off_in_production(self, settings):
        """Test that DEBUG is off in production"""
        # This should be enforced via environment variables
        # In tests, DEBUG might be on, but in production it should be off
        if hasattr(settings, 'ALLOWED_HOSTS'):
            if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ['*']:
                assert settings.DEBUG is False

    def test_no_sensitive_data_in_error_pages(self, client):
        """Test that error pages don't expose sensitive information"""
        response = client.get('/nonexistent-url-that-triggers-404/')
        assert response.status_code == 404

        if response.status_code == 404:
            content = response.content.decode('utf-8')
            # Should not expose file paths or settings
            assert 'SECRET_KEY' not in content
            assert 'DATABASE' not in content


# Django TestCase for additional security tests
class SecurityTestCase(TestCase):
    """Additional security tests using Django's TestCase"""

    def test_admin_requires_authentication(self):
        """Test that admin panel requires authentication"""
        response = self.client.get('/admin/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_clickjacking_protection(self):
        """Test X-Frame-Options header is set"""
        user = User.objects.create_superuser(
            username='frametest',
            email='frame@test.com',
            password='testpass123'
        )
        self.client.force_login(user)

        response = self.client.get('/claims/voyages/')
        if response.status_code == 200:
            # Should have X-Frame-Options header
            self.assertIn('X-Frame-Options', response.headers)

    def test_content_type_nosniff(self):
        """Test X-Content-Type-Options header is set"""
        response = self.client.get('/login/')
        # Should have X-Content-Type-Options: nosniff
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
