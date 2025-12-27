from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Voyages (NEW - Voyage Assignment)
    path('voyages/', views.voyage_list, name='voyage_list'),
    path('voyages/<int:pk>/', views.voyage_detail, name='voyage_detail'),
    path('voyages/<int:pk>/assign/', views.voyage_assign, name='voyage_assign'),
    path('voyages/<int:pk>/assign-to/', views.voyage_assign_to, name='voyage_assign_to'),
    path('voyages/<int:pk>/reassign/', views.voyage_reassign, name='voyage_reassign'),

    # Analytics (NEW)
    path('analytics/', views.analytics_dashboard, name='analytics'),

    # Claims
    path('claims/', views.claim_list, name='claim_list'),
    path('claims/create/', views.claim_create, name='claim_create'),
    path('claims/<int:pk>/', views.claim_detail, name='claim_detail'),
    path('claims/<int:pk>/edit/', views.claim_update, name='claim_update'),
    path('claims/<int:pk>/delete/', views.claim_delete, name='claim_delete'),
    path('claims/<int:pk>/status/', views.claim_status_update, name='claim_status_update'),

    # Comments
    path('claims/<int:claim_pk>/comment/', views.add_comment, name='add_comment'),

    # Documents
    path('claims/<int:claim_pk>/document/', views.add_document, name='add_document'),

    # Export
    path('claims/export/', views.export_claims, name='export_claims'),

    # User Profile
    path('users/', views.user_directory, name='user_directory'),
    path('users/export/', views.export_users, name='export_users'),
    path('users/<int:user_id>/', views.user_profile, name='user_profile'),
    path('users/<int:user_id>/edit/', views.user_profile_edit, name='user_profile_edit'),
    path('toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
]
