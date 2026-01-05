from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Claim, Comment, Document, Voyage, ShipOwner, VoyageAssignment, ClaimActivityLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'department', 'position', 'bio', 'profile_photo')}),
        ('Settings', {'fields': ('dark_mode', 'must_change_password')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'department', 'position')}),
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_staff', 'must_change_password']
    list_filter = ['role', 'is_staff', 'is_superuser', 'department', 'must_change_password']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def save_model(self, request, obj, form, change):
        """Set must_change_password=True for newly created users"""
        if not change:  # New user
            obj.must_change_password = True
        super().save_model(request, obj, form, change)


@admin.register(ShipOwner)
class ShipOwnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'contact_email', 'is_active', 'total_claims', 'total_voyages']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']

    def total_claims(self, obj):
        return obj.claims.count()
    total_claims.short_description = 'Total Claims'

    def total_voyages(self, obj):
        return obj.voyages.count()
    total_voyages.short_description = 'Total Voyages'


class ClaimInline(admin.TabularInline):
    model = Claim
    extra = 0
    fields = ['claim_number', 'claim_type', 'cost_type', 'status', 'payment_status', 'claim_amount', 'paid_amount']
    readonly_fields = ['claim_number']
    can_delete = False


class VoyageAssignmentInline(admin.TabularInline):
    model = VoyageAssignment
    extra = 0
    fields = ['assigned_to', 'assigned_by', 'assigned_at', 'unassigned_at', 'is_active', 'reassignment_reason']
    readonly_fields = ['assigned_at', 'unassigned_at']
    can_delete = False


@admin.register(Voyage)
class VoyageAdmin(admin.ModelAdmin):
    list_display = [
        'voyage_number', 'vessel_name', 'ship_owner', 'assignment_status',
        'assigned_analyst', 'total_claims', 'laycan_start', 'created_at'
    ]
    list_filter = ['assignment_status', 'ship_owner', 'assigned_analyst', 'created_at']
    search_fields = ['radar_voyage_id', 'voyage_number', 'vessel_name', 'imo_number', 'charter_party']
    readonly_fields = ['radar_voyage_id', 'last_radar_sync', 'created_at', 'updated_at', 'assigned_at', 'version']
    date_hierarchy = 'created_at'
    inlines = [VoyageAssignmentInline, ClaimInline]

    fieldsets = (
        ('RADAR Information', {
            'fields': ('radar_voyage_id', 'last_radar_sync', 'radar_data')
        }),
        ('Voyage Details', {
            'fields': (
                'voyage_number', 'vessel_name', 'imo_number', 'charter_party',
                'load_port', 'discharge_port', 'laycan_start', 'laycan_end'
            )
        }),
        ('Business Information', {
            'fields': ('ship_owner', 'demurrage_rate', 'laytime_allowed', 'currency')
        }),
        ('Assignment', {
            'fields': ('assignment_status', 'assigned_analyst', 'assigned_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_claims(self, obj):
        count = obj.claims.count()
        if count > 0:
            return format_html('<span style="font-weight: bold;">{}</span>', count)
        return count
    total_claims.short_description = 'Claims'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['user', 'created_at']


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    readonly_fields = ['uploaded_by', 'uploaded_at']


class ClaimActivityLogInline(admin.TabularInline):
    model = ClaimActivityLog
    extra = 0
    fields = ['action', 'user', 'message', 'old_value', 'new_value', 'created_at']
    readonly_fields = ['action', 'user', 'message', 'old_value', 'new_value', 'created_at']
    can_delete = False
    max_num = 20
    ordering = ['-created_at']


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = [
        'claim_number', 'voyage', 'ship_owner', 'claim_type', 'status',
        'payment_status', 'claim_amount', 'paid_amount', 'outstanding',
        'is_time_barred', 'assigned_to'
    ]
    list_filter = [
        'status', 'payment_status', 'claim_type', 'cost_type',
        'is_time_barred', 'ship_owner', 'assigned_to', 'created_at'
    ]
    search_fields = [
        'claim_number', 'radar_claim_id', 'voyage__voyage_number',
        'voyage__vessel_name', 'description'
    ]
    readonly_fields = [
        'claim_number', 'radar_claim_id', 'demurrage_days', 'outstanding_amount',
        'vessel_name', 'voyage_number', 'created_at', 'updated_at',
        'submitted_at', 'sent_to_owner_at', 'settled_at', 'paid_at',
        'last_radar_sync'
    ]
    date_hierarchy = 'created_at'
    inlines = [ClaimActivityLogInline, CommentInline, DocumentInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('claim_number', 'radar_claim_id', 'voyage', 'ship_owner')
        }),
        ('Claim Details', {
            'fields': (
                'claim_type', 'cost_type', 'status', 'payment_status',
                'claim_amount', 'paid_amount', 'outstanding_amount', 'currency'
            )
        }),
        ('Demurrage Calculation', {
            'fields': ('laytime_used', 'demurrage_days'),
            'classes': ('collapse',)
        }),
        ('Timebar & Deadlines', {
            'fields': ('claim_deadline', 'is_time_barred', 'time_bar_date')
        }),
        ('Notes', {
            'fields': ('description', 'internal_notes', 'settlement_notes')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('RADAR Sync', {
            'fields': ('last_radar_sync', 'radar_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'submitted_at',
                'sent_to_owner_at', 'settled_at', 'paid_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def outstanding(self, obj):
        amount = obj.outstanding_amount
        if amount > 0:
            return format_html('<span style="color: red; font-weight: bold;">{} {}</span>',
                             obj.currency, amount)
        return format_html('{} {}', obj.currency, amount)
    outstanding.short_description = 'Outstanding'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['claim', 'user', 'created_at', 'content_preview']
    list_filter = ['created_at']
    search_fields = ['content', 'claim__claim_number']
    readonly_fields = ['created_at', 'updated_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'claim', 'document_type', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['title', 'claim__claim_number', 'description']
    readonly_fields = ['uploaded_at']


@admin.register(VoyageAssignment)
class VoyageAssignmentAdmin(admin.ModelAdmin):
    list_display = ['voyage', 'assigned_to', 'assigned_by', 'assigned_at', 'unassigned_at', 'is_active', 'duration_days']
    list_filter = ['is_active', 'assigned_at', 'assigned_to', 'assigned_by']
    search_fields = ['voyage__voyage_number', 'voyage__vessel_name', 'assigned_to__username', 'assigned_by__username']
    readonly_fields = ['assigned_at', 'unassigned_at', 'duration', 'duration_days']
    date_hierarchy = 'assigned_at'

    fieldsets = (
        ('Assignment Details', {
            'fields': ('voyage', 'assigned_to', 'assigned_by', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('assigned_at', 'unassigned_at', 'duration', 'duration_days')
        }),
        ('Reassignment Info', {
            'fields': ('reassignment_reason',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ClaimActivityLog)
class ClaimActivityLogAdmin(admin.ModelAdmin):
    list_display = ['claim_number', 'action', 'user', 'message_preview', 'created_at']
    list_filter = ['action', 'created_at', 'user']
    search_fields = ['claim_number', 'claim__claim_number', 'message', 'user__username']
    readonly_fields = ['claim', 'claim_number', 'user', 'action', 'message', 'old_value', 'new_value', 'created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Activity Details', {
            'fields': ('claim', 'claim_number', 'user', 'action', 'created_at')
        }),
        ('Change Information', {
            'fields': ('message', 'old_value', 'new_value')
        }),
    )

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

    def has_add_permission(self, request):
        # Activity logs should only be created programmatically
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of audit trail
        return False
