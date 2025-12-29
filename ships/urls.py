from django.urls import path
from . import views

app_name = 'ships'

urlpatterns = [
    # TC Fleet URLs
    path('tc-fleet/', views.tc_fleet_list, name='tc_fleet_list'),
    path('tc-fleet/<int:pk>/', views.tc_fleet_detail, name='tc_fleet_detail'),
    path('tc-fleet/ship/<str:imo_number>/', views.tc_fleet_by_ship, name='tc_fleet_by_ship'),
    path('tc-fleet/export/', views.tc_fleet_export, name='tc_fleet_export'),
]
