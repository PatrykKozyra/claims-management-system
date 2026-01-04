"""
REST API Serializers for Claims Management System

These serializers handle conversion between Django models and JSON
for the REST API endpoints.
"""
from rest_framework import serializers
from claims.models import (
    User, ShipOwner, Voyage, Claim, VoyageAssignment,
    ClaimActivityLog, Comment, Document
)
from ships.models import Ship, TCFleet, ShipSpecification
from port_activities.models import ActivityType, PortActivity


# ============================================================================
# USER SERIALIZERS
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'department', 'phone', 'position',
            'dark_mode', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {'password': {'write_only': True}}

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserDetailSerializer(UserSerializer):
    """Detailed user serializer with additional info"""
    assigned_voyages_count = serializers.SerializerMethodField()
    assigned_claims_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'assigned_voyages_count', 'assigned_claims_count', 'bio'
        ]

    def get_assigned_voyages_count(self, obj):
        return obj.assigned_voyages.count()

    def get_assigned_claims_count(self, obj):
        return obj.assigned_claims.count()


# ============================================================================
# SHIP OWNER SERIALIZERS
# ============================================================================

class ShipOwnerSerializer(serializers.ModelSerializer):
    """Serializer for ShipOwner model"""
    voyages_count = serializers.SerializerMethodField()
    claims_count = serializers.SerializerMethodField()

    class Meta:
        model = ShipOwner
        fields = [
            'id', 'name', 'code', 'contact_email', 'contact_phone',
            'address', 'notes', 'is_active', 'voyages_count', 'claims_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_voyages_count(self, obj):
        return obj.voyages.count()

    def get_claims_count(self, obj):
        return obj.claims.count()


# ============================================================================
# VOYAGE SERIALIZERS
# ============================================================================

class VoyageListSerializer(serializers.ModelSerializer):
    """List serializer for Voyage model"""
    ship_owner_name = serializers.CharField(source='ship_owner.name', read_only=True)
    assigned_analyst_name = serializers.CharField(source='assigned_analyst.get_full_name', read_only=True)
    assignment_status_display = serializers.CharField(source='get_assignment_status_display', read_only=True)
    charter_type_display = serializers.CharField(source='get_charter_type_display', read_only=True)
    claims_count = serializers.SerializerMethodField()

    class Meta:
        model = Voyage
        fields = [
            'id', 'radar_voyage_id', 'voyage_number', 'vessel_name', 'imo_number',
            'charter_type', 'charter_type_display', 'charter_party',
            'load_port', 'discharge_port', 'laycan_start', 'laycan_end',
            'ship_owner', 'ship_owner_name', 'demurrage_rate', 'laytime_allowed',
            'currency', 'assignment_status', 'assignment_status_display',
            'assigned_analyst', 'assigned_analyst_name', 'assigned_at',
            'claims_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_radar_sync']

    def get_claims_count(self, obj):
        return obj.claims.count()


class VoyageDetailSerializer(VoyageListSerializer):
    """Detailed serializer for Voyage model"""
    ship_owner_details = ShipOwnerSerializer(source='ship_owner', read_only=True)
    assigned_analyst_details = UserSerializer(source='assigned_analyst', read_only=True)
    claims = serializers.SerializerMethodField()

    class Meta(VoyageListSerializer.Meta):
        fields = VoyageListSerializer.Meta.fields + [
            'ship_owner_details', 'assigned_analyst_details', 'claims',
            'last_radar_sync', 'radar_data', 'version'
        ]

    def get_claims(self, obj):
        from claims.serializers import ClaimListSerializer
        claims = obj.claims.all()[:10]  # Limit to 10 most recent
        return ClaimListSerializer(claims, many=True, context=self.context).data


# ============================================================================
# CLAIM SERIALIZERS
# ============================================================================

class ClaimListSerializer(serializers.ModelSerializer):
    """List serializer for Claim model"""
    voyage_number = serializers.CharField(source='voyage.voyage_number', read_only=True)
    vessel_name = serializers.CharField(source='voyage.vessel_name', read_only=True)
    ship_owner_name = serializers.CharField(source='ship_owner.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    claim_type_display = serializers.CharField(source='get_claim_type_display', read_only=True)
    outstanding_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Claim
        fields = [
            'id', 'claim_number', 'radar_claim_id', 'claim_type', 'claim_type_display',
            'cost_type', 'status', 'status_display', 'payment_status', 'payment_status_display',
            'voyage', 'voyage_number', 'vessel_name', 'ship_owner', 'ship_owner_name',
            'laytime_used', 'demurrage_days', 'claim_amount', 'paid_amount', 'outstanding_amount',
            'currency', 'claim_deadline', 'is_time_barred', 'time_bar_date',
            'assigned_to', 'assigned_to_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'claim_number', 'demurrage_days', 'created_at', 'updated_at']


class ClaimDetailSerializer(ClaimListSerializer):
    """Detailed serializer for Claim model"""
    voyage_details = VoyageListSerializer(source='voyage', read_only=True)
    ship_owner_details = ShipOwnerSerializer(source='ship_owner', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    activity_logs = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()

    class Meta(ClaimListSerializer.Meta):
        fields = ClaimListSerializer.Meta.fields + [
            'voyage_details', 'ship_owner_details', 'assigned_to_details', 'created_by_details',
            'description', 'settlement_notes', 'internal_notes',
            'activity_logs', 'comments_count', 'documents_count',
            'last_radar_sync', 'version', 'submitted_at', 'sent_to_owner_at',
            'settled_at', 'paid_at'
        ]

    def get_activity_logs(self, obj):
        logs = obj.activity_logs.all()[:20]  # Limit to 20 most recent
        return ClaimActivityLogSerializer(logs, many=True, context=self.context).data

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_documents_count(self, obj):
        return obj.documents.count()


# ============================================================================
# VOYAGE ASSIGNMENT SERIALIZERS
# ============================================================================

class VoyageAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for VoyageAssignment model"""
    voyage_number = serializers.CharField(source='voyage.voyage_number', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = VoyageAssignment
        fields = [
            'id', 'voyage', 'voyage_number', 'assigned_to', 'assigned_to_name',
            'assigned_by', 'assigned_by_name', 'assigned_at', 'unassigned_at',
            'is_active', 'reassignment_reason', 'duration_days'
        ]
        read_only_fields = ['id', 'assigned_at']


# ============================================================================
# ACTIVITY LOG SERIALIZERS
# ============================================================================

class ClaimActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ClaimActivityLog model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    action_icon = serializers.CharField(read_only=True)
    action_color = serializers.CharField(read_only=True)

    class Meta:
        model = ClaimActivityLog
        fields = [
            'id', 'claim', 'claim_number', 'user', 'user_name',
            'action', 'action_display', 'action_icon', 'action_color',
            'message', 'old_value', 'new_value', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ============================================================================
# COMMENT SERIALIZERS
# ============================================================================

class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'claim', 'user', 'user_name', 'content',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# DOCUMENT SERIALIZERS
# ============================================================================

class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    filename = serializers.CharField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'claim', 'title', 'document_type', 'document_type_display',
            'file', 'file_url', 'filename', 'uploaded_by', 'uploaded_by_name',
            'uploaded_at', 'description'
        ]
        read_only_fields = ['id', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


# ============================================================================
# SHIP SERIALIZERS
# ============================================================================

class ShipSerializer(serializers.ModelSerializer):
    """Serializer for Ship model"""
    is_charter_active = serializers.BooleanField(read_only=True)
    charter_days_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = Ship
        fields = [
            'id', 'imo_number', 'vessel_name', 'vessel_type', 'flag', 'built_year',
            'deadweight', 'gross_tonnage', 'engine_type', 'cargo_capacity',
            'is_tc_fleet', 'charter_type', 'charter_start_date', 'charter_end_date',
            'daily_hire_rate', 'tc_charterer', 'is_charter_active',
            'charter_days_remaining', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# PORT ACTIVITY SERIALIZERS
# ============================================================================

class ActivityTypeSerializer(serializers.ModelSerializer):
    """Serializer for ActivityType model"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ActivityType
        fields = [
            'id', 'code', 'name', 'category', 'category_display',
            'description', 'is_active', 'icon_class', 'color_class'
        ]
        read_only_fields = ['id']


class PortActivitySerializer(serializers.ModelSerializer):
    """Serializer for PortActivity model"""
    ship_name = serializers.CharField(source='ship.vessel_name', read_only=True)
    activity_type_name = serializers.CharField(source='activity_type.name', read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    is_fully_actual = serializers.BooleanField(read_only=True)
    date_status_display = serializers.CharField(read_only=True)

    class Meta:
        model = PortActivity
        fields = [
            'id', 'ship', 'ship_name', 'voyage', 'activity_type', 'activity_type_name',
            'load_port', 'discharge_port', 'port_name',
            'start_datetime', 'start_date_status', 'end_datetime', 'end_date_status',
            'duration', 'duration_hours', 'duration_days',
            'is_fully_actual', 'date_status_display',
            'cargo_quantity', 'notes', 'user_comments',
            'radar_activity_id', 'last_radar_sync',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'duration', 'created_at', 'updated_at']


# ============================================================================
# ANALYTICS SERIALIZERS
# ============================================================================

class ClaimAnalyticsSerializer(serializers.Serializer):
    """Serializer for claim analytics data"""
    total_claims = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    by_status = serializers.DictField()
    by_payment_status = serializers.DictField()
    by_claim_type = serializers.DictField()
    timebarred_claims = serializers.IntegerField()


class VoyageAnalyticsSerializer(serializers.Serializer):
    """Serializer for voyage analytics data"""
    total_voyages = serializers.IntegerField()
    assigned_voyages = serializers.IntegerField()
    unassigned_voyages = serializers.IntegerField()
    completed_voyages = serializers.IntegerField()
    by_charter_type = serializers.DictField()
    by_assignment_status = serializers.DictField()
