"""
REST API ViewSets for Claims Management System

These viewsets provide RESTful API endpoints for all models.
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from django.utils import timezone

from claims.models import (
    User, ShipOwner, Voyage, Claim, VoyageAssignment,
    ClaimActivityLog, Comment, Document
)
from ships.models import Ship
from port_activities.models import ActivityType, PortActivity
from claims.serializers import (
    UserSerializer, UserDetailSerializer,
    ShipOwnerSerializer,
    VoyageListSerializer, VoyageDetailSerializer,
    ClaimListSerializer, ClaimDetailSerializer,
    VoyageAssignmentSerializer,
    ClaimActivityLogSerializer,
    CommentSerializer,
    DocumentSerializer,
    ShipSerializer,
    ActivityTypeSerializer,
    PortActivitySerializer,
    ClaimAnalyticsSerializer,
    VoyageAnalyticsSerializer,
)


# ============================================================================
# CUSTOM PERMISSIONS
# ============================================================================

class IsAdminOrReadOnly(IsAuthenticated):
    """Only admins can modify, others can read"""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user.is_admin_role()


class CanWritePermission(IsAuthenticated):
    """Only users with write permission can modify"""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user.can_write()


# ============================================================================
# USER VIEWSETS
# ============================================================================

class UserViewSet(viewsets.ModelViewSet):
    """API endpoint for users"""
    queryset = User.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'department']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'date_joined', 'last_login']
    ordering = ['username']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user info"""
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def analysts(self, request):
        """Get list of analysts (users who can be assigned voyages/claims)"""
        analysts = User.objects.filter(
            role__in=['WRITE', 'TEAM_LEAD', 'ADMIN'],
            is_active=True
        )
        serializer = self.get_serializer(analysts, many=True)
        return Response(serializer.data)


# ============================================================================
# SHIP OWNER VIEWSETS
# ============================================================================

class ShipOwnerViewSet(viewsets.ModelViewSet):
    """API endpoint for ship owners"""
    queryset = ShipOwner.objects.all()
    serializer_class = ShipOwnerSerializer
    permission_classes = [CanWritePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'contact_email']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def voyages(self, request, pk=None):
        """Get all voyages for a ship owner"""
        owner = self.get_object()
        voyages = owner.voyages.all()
        serializer = VoyageListSerializer(voyages, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def claims(self, request, pk=None):
        """Get all claims for a ship owner"""
        owner = self.get_object()
        claims = owner.claims.all()
        serializer = ClaimListSerializer(claims, many=True, context={'request': request})
        return Response(serializer.data)


# ============================================================================
# VOYAGE VIEWSETS
# ============================================================================

class VoyageViewSet(viewsets.ModelViewSet):
    """API endpoint for voyages"""
    queryset = Voyage.objects.select_related('ship_owner', 'assigned_analyst').all()
    permission_classes = [CanWritePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assignment_status', 'charter_type', 'ship_owner', 'assigned_analyst']
    search_fields = ['voyage_number', 'vessel_name', 'imo_number', 'charter_party']
    ordering_fields = ['created_at', 'laycan_start', 'voyage_number']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VoyageDetailSerializer
        return VoyageListSerializer

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign voyage to an analyst"""
        voyage = self.get_object()
        analyst_id = request.data.get('analyst_id')

        if not analyst_id:
            return Response(
                {'error': 'analyst_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            analyst = User.objects.get(id=analyst_id, role__in=['WRITE', 'TEAM_LEAD', 'ADMIN'])
            voyage.assign_to(analyst, assigned_by=request.user)

            return Response({
                'status': 'success',
                'message': f'Voyage assigned to {analyst.get_full_name()}'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid analyst ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def unassigned(self, request):
        """Get unassigned voyages"""
        voyages = self.queryset.filter(assignment_status='UNASSIGNED')
        serializer = self.get_serializer(voyages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """Get voyages assigned to current user"""
        voyages = self.queryset.filter(assigned_analyst=request.user)
        serializer = self.get_serializer(voyages, many=True)
        return Response(serializer.data)


# ============================================================================
# CLAIM VIEWSETS
# ============================================================================

class ClaimViewSet(viewsets.ModelViewSet):
    """API endpoint for claims"""
    queryset = Claim.objects.select_related(
        'voyage', 'ship_owner', 'assigned_to', 'created_by'
    ).all()
    permission_classes = [CanWritePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'payment_status', 'claim_type', 'cost_type',
        'voyage', 'ship_owner', 'assigned_to', 'is_time_barred'
    ]
    search_fields = ['claim_number', 'radar_claim_id', 'description']
    ordering_fields = ['created_at', 'claim_amount', 'claim_deadline']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClaimDetailSerializer
        return ClaimListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a claim"""
        claim = self.get_object()

        if claim.status != 'DRAFT':
            return Response(
                {'error': 'Only draft claims can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        claim.status = 'SUBMITTED'
        claim.submitted_at = timezone.now()
        claim.save()

        # Log activity
        ClaimActivityLog.objects.create(
            claim=claim,
            claim_number=claim.claim_number,
            user=request.user,
            action='STATUS_CHANGED',
            message='Claim submitted',
            old_value='DRAFT',
            new_value='SUBMITTED'
        )

        return Response({
            'status': 'success',
            'message': 'Claim submitted successfully'
        })

    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """Record a payment for a claim"""
        claim = self.get_object()
        amount = request.data.get('amount')

        if not amount:
            return Response(
                {'error': 'Payment amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from decimal import Decimal
            payment_amount = Decimal(amount)

            if payment_amount <= 0:
                return Response(
                    {'error': 'Payment amount must be positive'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            old_paid_amount = claim.paid_amount
            claim.paid_amount += payment_amount

            # Update payment status
            if claim.paid_amount >= claim.claim_amount:
                claim.payment_status = 'PAID'
                claim.paid_at = timezone.now()
            elif claim.paid_amount > 0:
                claim.payment_status = 'PARTIALLY_PAID'

            claim.save()

            # Log activity
            ClaimActivityLog.objects.create(
                claim=claim,
                claim_number=claim.claim_number,
                user=request.user,
                action='PAID_AMOUNT_CHANGED',
                message=f'Payment of ${payment_amount:,.2f} recorded',
                old_value=str(old_paid_amount),
                new_value=str(claim.paid_amount)
            )

            return Response({
                'status': 'success',
                'message': f'Payment of ${payment_amount:,.2f} recorded',
                'paid_amount': claim.paid_amount,
                'outstanding_amount': claim.outstanding_amount
            })

        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid payment amount'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def timebarred(self, request):
        """Get time-barred claims"""
        claims = self.queryset.filter(is_time_barred=True)
        serializer = self.get_serializer(claims, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_claims(self, request):
        """Get claims assigned to current user"""
        claims = self.queryset.filter(assigned_to=request.user)
        serializer = self.get_serializer(claims, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get claim analytics"""
        queryset = self.filter_queryset(self.get_queryset())

        analytics_data = {
            'total_claims': queryset.count(),
            'total_amount': queryset.aggregate(Sum('claim_amount'))['claim_amount__sum'] or 0,
            'paid_amount': queryset.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0,
            'outstanding_amount': sum(c.outstanding_amount for c in queryset),
            'by_status': dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_payment_status': dict(queryset.values('payment_status').annotate(count=Count('id')).values_list('payment_status', 'count')),
            'by_claim_type': dict(queryset.values('claim_type').annotate(count=Count('id')).values_list('claim_type', 'count')),
            'timebarred_claims': queryset.filter(is_time_barred=True).count(),
        }

        serializer = ClaimAnalyticsSerializer(analytics_data)
        return Response(serializer.data)


# ============================================================================
# ACTIVITY LOG VIEWSETS
# ============================================================================

class ClaimActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for claim activity logs (read-only)"""
    queryset = ClaimActivityLog.objects.select_related('claim', 'user').all()
    serializer_class = ClaimActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['claim', 'user', 'action']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


# ============================================================================
# COMMENT VIEWSETS
# ============================================================================

class CommentViewSet(viewsets.ModelViewSet):
    """API endpoint for comments"""
    queryset = Comment.objects.select_related('claim', 'user').all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['claim', 'user']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ============================================================================
# DOCUMENT VIEWSETS
# ============================================================================

class DocumentViewSet(viewsets.ModelViewSet):
    """API endpoint for documents"""
    queryset = Document.objects.select_related('claim', 'uploaded_by').all()
    serializer_class = DocumentSerializer
    permission_classes = [CanWritePermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['claim', 'document_type', 'uploaded_by']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


# ============================================================================
# SHIP VIEWSETS
# ============================================================================

class ShipViewSet(viewsets.ModelViewSet):
    """API endpoint for ships"""
    queryset = Ship.objects.all()
    serializer_class = ShipSerializer
    permission_classes = [CanWritePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_tc_fleet', 'charter_type', 'vessel_type', 'flag']
    search_fields = ['imo_number', 'vessel_name', 'owner_name']
    ordering_fields = ['vessel_name', 'built_year', 'deadweight']
    ordering = ['vessel_name']

    @action(detail=False, methods=['get'])
    def active_charters(self, request):
        """Get ships with active time charters"""
        ships = self.queryset.filter(is_tc_fleet=True)
        ships = [s for s in ships if s.is_charter_active]
        serializer = self.get_serializer(ships, many=True)
        return Response(serializer.data)


# ============================================================================
# PORT ACTIVITY VIEWSETS
# ============================================================================

class ActivityTypeViewSet(viewsets.ModelViewSet):
    """API endpoint for activity types"""
    queryset = ActivityType.objects.all()
    serializer_class = ActivityTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['name', 'category']
    ordering = ['category', 'name']


class PortActivityViewSet(viewsets.ModelViewSet):
    """API endpoint for port activities"""
    queryset = PortActivity.objects.select_related(
        'ship', 'voyage', 'activity_type', 'created_by'
    ).all()
    serializer_class = PortActivitySerializer
    permission_classes = [CanWritePermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['ship', 'voyage', 'activity_type', 'start_date_status', 'end_date_status']
    ordering_fields = ['start_datetime', 'created_at']
    ordering = ['-start_datetime']

    @action(detail=False, methods=['get'])
    def ship_timeline(self, request):
        """Get timeline of activities for a specific ship"""
        ship_id = request.query_params.get('ship_id')

        if not ship_id:
            return Response(
                {'error': 'ship_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        activities = self.queryset.filter(ship_id=ship_id).order_by('start_datetime')
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)
