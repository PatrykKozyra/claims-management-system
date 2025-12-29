from django.urls import path
from . import views

app_name = 'port_activities'

urlpatterns = [
    # Activity List Views
    path('', views.activity_list_all, name='activity_list_all'),
    path('ship/<str:imo_number>/', views.activity_list_by_ship, name='activity_list_by_ship'),
    path('voyage/<int:voyage_id>/', views.activity_list_by_voyage, name='activity_list_by_voyage'),

    # Activity CRUD
    path('create/', views.activity_create, name='activity_create'),
    path('<int:pk>/', views.activity_detail, name='activity_detail'),
    path('<int:pk>/edit/', views.activity_update, name='activity_update'),
    path('<int:pk>/delete/', views.activity_delete, name='activity_delete'),

    # Export
    path('export/', views.activity_export, name='activity_export'),
]
