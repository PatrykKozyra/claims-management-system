"""
REST API URL Configuration

This module defines the URL routing for the REST API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from claims.api_views import (
    UserViewSet,
    ShipOwnerViewSet,
    VoyageViewSet,
    ClaimViewSet,
    ClaimActivityLogViewSet,
    CommentViewSet,
    DocumentViewSet,
    ShipViewSet,
    ActivityTypeViewSet,
    PortActivityViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'ship-owners', ShipOwnerViewSet, basename='shipowner')
router.register(r'voyages', VoyageViewSet, basename='voyage')
router.register(r'claims', ClaimViewSet, basename='claim')
router.register(r'activity-logs', ClaimActivityLogViewSet, basename='activitylog')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'ships', ShipViewSet, basename='ship')
router.register(r'activity-types', ActivityTypeViewSet, basename='activitytype')
router.register(r'port-activities', PortActivityViewSet, basename='portactivity')

# URL patterns
urlpatterns = [
    # API router
    path('', include(router.urls)),

    # Token Authentication (Simple Token)
    path('auth/token/', obtain_auth_token, name='api-token-auth'),

    # JWT Authentication
    path('auth/jwt/create/', TokenObtainPairView.as_view(), name='jwt-create'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    path('auth/jwt/verify/', TokenVerifyView.as_view(), name='jwt-verify'),

    # Browsable API authentication
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]
