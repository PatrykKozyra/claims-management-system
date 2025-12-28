from django.contrib import admin
from django.utils.html import format_html
from .models import Ship


@admin.register(Ship)
class ShipAdmin(admin.ModelAdmin):
    list_display = [
        'vessel_name', 'imo_number', 'vessel_type', 'charter_type',
        'is_tc_fleet', 'tc_status', 'built_year', 'flag', 'is_active'
    ]
    list_filter = [
        'is_active', 'is_tc_fleet', 'charter_type', 'vessel_type',
        'flag', 'built_year'
    ]
    search_fields = ['vessel_name', 'imo_number', 'tc_charterer']
    readonly_fields = ['created_at', 'updated_at', 'last_sync', 'charter_status_display']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Vessel Identification', {
            'fields': ('imo_number', 'vessel_name', 'vessel_type', 'flag')
        }),
        ('Technical Specifications', {
            'fields': (
                'built_year', 'deadweight', 'gross_tonnage',
                'engine_type', 'engine_power', 'cargo_capacity'
            )
        }),
        ('Charter Information', {
            'fields': (
                'charter_type', 'is_tc_fleet', 'charter_start_date', 'charter_end_date',
                'daily_hire_rate', 'tc_charterer', 'charter_status_display'
            )
        }),
        ('Status & Sync', {
            'fields': ('is_active', 'external_db_id', 'last_sync', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def tc_status(self, obj):
        """Display TC status with visual indicator"""
        if not obj.is_tc_fleet:
            return format_html('<span style="color: gray;">-</span>')

        if obj.is_charter_active:
            days_left = obj.charter_days_remaining
            if days_left <= 30:
                color = 'red'
                status = f'Expiring ({days_left}d)'
            elif days_left <= 90:
                color = 'orange'
                status = f'Active ({days_left}d)'
            else:
                color = 'green'
                status = f'Active ({days_left}d)'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, status
            )
        else:
            return format_html('<span style="color: gray;">Inactive</span>')

    tc_status.short_description = 'TC Status'

    def charter_status_display(self, obj):
        """Detailed charter status for detail view"""
        if not obj.is_tc_fleet:
            return 'Not part of TC fleet'

        if obj.is_charter_active:
            return format_html(
                '<strong style="color: green;">ACTIVE</strong><br>'
                'Days remaining: {} days<br>'
                'Expires: {}',
                obj.charter_days_remaining,
                obj.charter_end_date.strftime('%Y-%m-%d')
            )
        else:
            return format_html('<strong style="color: gray;">INACTIVE</strong>')

    charter_status_display.short_description = 'Charter Status'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().getqueryset(request)
        return qs

    class Media:
        css = {
            'all': ('admin/css/custom_ship_admin.css',)
        }
