from django.contrib import admin
from django.utils.html import format_html
from .models import ActivityType, PortActivity


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']


@admin.register(PortActivity)
class PortActivityAdmin(admin.ModelAdmin):
    list_display = [
        'ship', 'voyage', 'activity_type', 'port_name',
        'start_date_display', 'end_date_display', 'duration_display',
        'date_status_badge', 'created_at'
    ]
    list_filter = [
        'activity_type__category', 'activity_type', 'start_date_status',
        'end_date_status', 'created_at'
    ]
    search_fields = [
        'ship__vessel_name', 'ship__imo_number', 'voyage__voyage_number',
        'port_name', 'load_port', 'discharge_port', 'radar_activity_id'
    ]
    readonly_fields = [
        'duration', 'created_by', 'created_at', 'updated_at',
        'last_radar_sync', 'duration_display'
    ]
    date_hierarchy = 'start_datetime'
    autocomplete_fields = ['ship', 'voyage']

    fieldsets = (
        ('Activity Information', {
            'fields': ('ship', 'voyage', 'activity_type')
        }),
        ('Port Details', {
            'fields': ('port_name', 'load_port', 'discharge_port')
        }),
        ('Timeline', {
            'fields': (
                ('start_datetime', 'start_date_status'),
                ('end_datetime', 'end_date_status'),
                'duration', 'duration_display'
            )
        }),
        ('Additional Info', {
            'fields': ('cargo_quantity', 'notes')
        }),
        ('RADAR Sync', {
            'fields': ('radar_activity_id', 'last_radar_sync'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def start_date_display(self, obj):
        """Display start date with status indicator"""
        if obj.start_date_status == 'ACTUAL':
            color = 'green'
            icon = '✓'
        else:
            color = 'orange'
            icon = '~'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.start_datetime.strftime('%Y-%m-%d %H:%M')
        )
    start_date_display.short_description = 'Start Date'

    def end_date_display(self, obj):
        """Display end date with status indicator"""
        if obj.end_date_status == 'ACTUAL':
            color = 'green'
            icon = '✓'
        else:
            color = 'orange'
            icon = '~'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.end_datetime.strftime('%Y-%m-%d %H:%M')
        )
    end_date_display.short_description = 'End Date'

    def duration_display(self, obj):
        """Display duration in days and hours"""
        if not obj.duration:
            return '-'
        days = obj.duration_days
        hours = obj.duration_hours % 24
        return format_html(
            '<strong>{}</strong> days, <strong>{:.1f}</strong> hours',
            days, hours
        )
    duration_display.short_description = 'Duration'

    def date_status_badge(self, obj):
        """Display date status as a badge"""
        if obj.is_fully_actual:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">ACTUAL</span>'
            )
        elif obj.is_fully_estimated:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 8px; border-radius: 3px;">ESTIMATED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 3px 8px; border-radius: 3px;">MIXED</span>'
            )
    date_status_badge.short_description = 'Date Status'

    def save_model(self, request, obj, form, change):
        """Auto-set created_by on create"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'ship', 'voyage', 'activity_type', 'created_by'
        )
