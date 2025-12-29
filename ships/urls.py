from django.urls import path
from . import views

app_name = 'ships'

urlpatterns = [
    # TC Fleet URLs
    path('tc-fleet/', views.tc_fleet_list, name='tc_fleet_list'),
    path('tc-fleet/<int:pk>/', views.tc_fleet_detail, name='tc_fleet_detail'),
    path('tc-fleet/ship/<str:imo_number>/', views.tc_fleet_by_ship, name='tc_fleet_by_ship'),
    path('tc-fleet/export/', views.tc_fleet_export, name='tc_fleet_export'),

    # Ship Specifications (Q88) URLs
    path('ship-specifications/', views.ship_specifications_list, name='ship_specifications_list'),
    path('ship-specifications/<str:imo_number>/', views.ship_specification_detail, name='ship_specification_detail'),
    path('ship-specifications/export/', views.ship_specifications_export, name='ship_specifications_export'),
]
