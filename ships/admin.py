from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Ship, TCFleet, ShipSpecification


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
        qs = super().get_queryset(request)
        return qs

    class Media:
        css = {
            'all': ('admin/css/custom_ship_admin.css',)
        }


@admin.register(TCFleet)
class TCFleetAdmin(admin.ModelAdmin):
    list_display = [
        'ship_name', 'imo_number', 'radar_deal_number', 'ship_type',
        'delivery_status_badge', 'trade', 'owner_name', 'trader_name',
        'delivery_date_formatted', 'redelivery_date_formatted',
        'tc_rate_monthly', 'days_remaining_display', 'contract_status_badge'
    ]
    list_filter = [
        'delivery_status', 'ship_type', 'trade', 'owner_name',
        'trader_name', 'flag', 'built_year'
    ]
    search_fields = [
        'ship_name', 'imo_number', 'radar_deal_number', 'owner_name',
        'trader_name', 'broker_name', 'technical_manager'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'contract_status',
        'days_remaining', 'charter_length_months', 'total_contract_value',
        'ship_name_change_indicator'
    ]
    date_hierarchy = 'delivery_date'

    fieldsets = (
        ('Ship Identification', {
            'fields': (
                'ship_name', 'imo_number', 'ship_type', 'ship_name_change_indicator'
            )
        }),
        ('Contract Status', {
            'fields': (
                'delivery_status', 'trade', 'radar_deal_number', 'contract_status'
            )
        }),
        ('Owner & Technical Manager', {
            'fields': (
                ('owner_name', 'owner_email'),
                ('technical_manager', 'technical_manager_email')
            )
        }),
        ('Charter Details', {
            'fields': (
                ('charter_length_years', 'charter_length_months'),
                ('tc_rate_monthly', 'total_contract_value')
            )
        }),
        ('Important Dates', {
            'fields': (
                ('delivery_date', 'redelivery_date', 'tcp_date'),
                'days_remaining'
            )
        }),
        ('Broker Information', {
            'fields': (
                'broker_name', 'broker_email', 'broker_commission'
            ),
            'classes': ('collapse',)
        }),
        ('Locations', {
            'fields': (
                'delivery_location', 'redelivery_location'
            )
        }),
        ('Technical Specifications', {
            'fields': (
                'bunkers_policy', 'summer_dwt', 'built_year',
                'flag', 'next_drydock_date'
            ),
            'classes': ('collapse',)
        }),
        ('Internal Information', {
            'fields': (
                'trader_name', 'notes'
            )
        }),
        ('Audit', {
            'fields': (
                'created_at', 'updated_at', 'created_by'
            ),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Auto-populate created_by field"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def delivery_status_badge(self, obj):
        """Display delivery status with color coding"""
        colors = {
            'INCOMING_TC': '#17a2b8',  # cyan
            'ON_TC': '#28a745',  # green
            'REDELIVERED': '#6c757d',  # gray
        }
        color = colors.get(obj.delivery_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 0.85em; font-weight: 600;">{}</span>',
            color, obj.get_delivery_status_display()
        )
    delivery_status_badge.short_description = 'Delivery Status'

    def contract_status_badge(self, obj):
        """Display calculated contract status with color coding"""
        status = obj.contract_status
        colors = {
            'ACTIVE': '#28a745',  # green
            'INCOMING': '#17a2b8',  # cyan
            'EXPIRING_SOON': '#ffc107',  # yellow
            'EXPIRED': '#dc3545',  # red
            'COMPLETED': '#6c757d',  # gray
            'UNKNOWN': '#6c757d',  # gray
        }
        color = colors.get(status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-size: 0.85em; font-weight: 600;">{}</span>',
            color,
            'black' if status == 'EXPIRING_SOON' else 'white',
            status.replace('_', ' ')
        )
    contract_status_badge.short_description = 'Contract Status'

    def delivery_date_formatted(self, obj):
        """Format delivery date as dd/mm/yyyy"""
        return obj.delivery_date.strftime('%d/%m/%Y')
    delivery_date_formatted.short_description = 'Delivery Date'
    delivery_date_formatted.admin_order_field = 'delivery_date'

    def redelivery_date_formatted(self, obj):
        """Format redelivery date as dd/mm/yyyy"""
        return obj.redelivery_date.strftime('%d/%m/%Y')
    redelivery_date_formatted.short_description = 'Redelivery Date'
    redelivery_date_formatted.admin_order_field = 'redelivery_date'

    def days_remaining_display(self, obj):
        """Display days remaining with color coding"""
        days = obj.days_remaining
        if days == 0:
            return format_html('<span style="color: gray;">-</span>')
        elif days <= 30:
            color = 'red'
        elif days <= 90:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} days</span>',
            color, days
        )
    days_remaining_display.short_description = 'Days Left'

    def ship_name_change_indicator(self, obj):
        """Show if ship name has changed"""
        current_name = obj.get_current_ship_name()
        if current_name:
            return format_html(
                '<div style="padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107;">'
                '<strong>⚠️ Ship Name Changed</strong><br>'
                'Contract Name: <strong>{}</strong><br>'
                'Current Name: <strong>{}</strong><br>'
                '<small>IMO {} remains the same</small>'
                '</div>',
                obj.ship_name, current_name, obj.imo_number
            )
        return format_html(
            '<span style="color: green;">✓ No name change detected</span>'
        )
    ship_name_change_indicator.short_description = 'Ship Name Status'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('created_by')

    class Media:
        css = {
            'all': ('admin/css/custom_ship_admin.css',)
        }


@admin.register(ShipSpecification)
class ShipSpecificationAdmin(admin.ModelAdmin):
    """Admin interface for Ship Specifications (Q88)"""

    list_display = [
        'vessel_name',
        'imo_number',
        'vessel_type_badge',
        'built_year',
        'flag',
        'summer_deadweight',
        'has_active_contract',
        'updated_at',
    ]

    list_filter = [
        'vessel_type',
        'built_year',
        'flag',
        'cargo_tank_coating',
        'fuel_type',
        'double_hull',
        'inert_gas_system',
        'crude_oil_washing',
    ]

    search_fields = [
        'vessel_name',
        'imo_number',
        'call_sign',
        'owner_name',
        'technical_manager',
        'classification_society',
    ]

    readonly_fields = [
        'displacement',
        'cargo_capacity_per_tank',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Vessel Identification', {
            'fields': (
                ('vessel_name', 'imo_number'),
                ('call_sign', 'flag'),
                ('port_of_registry', 'official_number'),
                ('vessel_type', 'built_year'),
                ('built_country', 'shipyard'),
                ('classification_society', 'class_notation'),
            )
        }),
        ('Dimensions & Tonnages', {
            'fields': (
                ('length_overall', 'length_between_perpendiculars'),
                ('breadth_moulded', 'depth_moulded'),
                ('summer_draft', 'summer_deadweight'),
                ('lightweight', 'displacement'),
                ('gross_tonnage', 'net_tonnage'),
                ('suez_canal_tonnage', 'panama_canal_tonnage'),
            )
        }),
        ('Cargo Capacity', {
            'fields': (
                ('total_cargo_capacity', 'number_of_cargo_tanks'),
                'cargo_capacity_per_tank',
                ('segregated_ballast_tanks_capacity', 'slop_tank_capacity'),
                ('cargo_tank_coating', 'cargo_heating_capability'),
                'maximum_heating_temperature',
            )
        }),
        ('Machinery & Performance', {
            'fields': (
                ('main_engine_type', 'main_engine_builder'),
                'main_engine_power',
                ('service_speed_laden', 'service_speed_ballast'),
                ('fuel_consumption_laden', 'fuel_consumption_ballast'),
                ('fuel_type', 'bow_thruster', 'stern_thruster'),
            )
        }),
        ('Cargo Handling', {
            'fields': (
                ('number_of_cargo_pumps', 'cargo_pump_capacity'),
                ('inert_gas_system', 'crude_oil_washing', 'vapor_recovery_system'),
                ('cargo_manifold_size', 'cargo_manifold_pressure_rating'),
            )
        }),
        ('Environmental & Safety', {
            'fields': (
                ('double_hull', 'ice_class'),
                'oil_pollution_prevention_certificate_expiry',
                'safety_management_certificate_expiry',
                'safety_equipment_certificate_expiry',
                'international_oil_pollution_certificate_expiry',
                'ship_sanitation_certificate_expiry',
            )
        }),
        ('Operational Requirements', {
            'fields': (
                ('minimum_freeboard_laden', 'maximum_allowed_draft_restriction'),
                ('air_draft_ballast', 'air_draft_laden'),
                'port_restrictions',
                'special_requirements',
            )
        }),
        ('Commercial', {
            'fields': (
                ('owner_name', 'operator_name'),
                ('commercial_manager', 'technical_manager'),
                'p_and_i_club',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',)
        }),
    )

    def vessel_type_badge(self, obj):
        """Display vessel type with color badge"""
        colors = {
            'CRUDE': '#dc3545',
            'PRODUCT': '#0d6efd',
            'CHEMICAL': '#ffc107',
        }
        color = colors.get(obj.vessel_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_vessel_type_display()
        )
    vessel_type_badge.short_description = 'Vessel Type'

    def has_active_contract(self, obj):
        """Show if vessel has active TC contract"""
        contract = obj.get_active_tc_contract()
        if contract:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ On TC</span><br>'
                '<small>Until {}</small>',
                contract.redelivery_date.strftime('%d/%m/%Y')
            )
        return format_html('<span style="color: gray;">No active contract</span>')
    has_active_contract.short_description = 'TC Status'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('created_by')
