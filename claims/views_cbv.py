"""
Class-Based Views for Claims Management System

This module contains refactored CBVs for better code organization and reusability.
Gradually migrating from function-based views in views.py
"""
from __future__ import annotations
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count, Sum, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from .models import Claim, Voyage, ShipOwner, Comment, Document, User, ClaimActivityLog
from .forms import ClaimForm, CommentForm, DocumentForm, ClaimStatusForm


# ============================================================================
# PERMISSION MIXINS
# ============================================================================

class CanWriteMixin(UserPassesTestMixin):
    """Mixin to restrict access to users with write permissions"""

    def test_func(self) -> bool:
        return self.request.user.can_write()

    def handle_no_permission(self) -> HttpResponse:
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('dashboard')


class CanExportMixin(UserPassesTestMixin):
    """Mixin to restrict access to users with export permissions"""

    def test_func(self) -> bool:
        return self.request.user.can_export()

    def handle_no_permission(self) -> HttpResponse:
        messages.error(self.request, "You don't have permission to export data.")
        return redirect('dashboard')


class IsAdminMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin users"""

    def test_func(self) -> bool:
        return self.request.user.is_admin_role()

    def handle_no_permission(self) -> HttpResponse:
        messages.error(self.request, "Admin access required.")
        return redirect('dashboard')


# ============================================================================
# DASHBOARD VIEW
# ============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with statistics and recent claims"""
    template_name = 'claims/dashboard.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's claims queryset
        my_claims_queryset = Claim.objects.filter(
            Q(created_by=user) | Q(assigned_to=user)
        ).distinct().select_related('voyage', 'ship_owner')

        # Statistics
        stats = {
            'total_claims': my_claims_queryset.count(),
            'draft_claims': my_claims_queryset.filter(status='DRAFT').count(),
            'under_review': my_claims_queryset.filter(status='UNDER_REVIEW').count(),
            'submitted': my_claims_queryset.filter(status='SUBMITTED').count(),
            'settled': my_claims_queryset.filter(status='SETTLED').count(),
            'time_barred': my_claims_queryset.filter(is_time_barred=True).count(),
            'not_sent': my_claims_queryset.filter(payment_status='NOT_SENT').count(),
        }

        # Voyage statistics for analysts
        if user.can_write():
            my_voyages = Voyage.objects.filter(assigned_analyst=user)
            unassigned_voyages = Voyage.objects.filter(assignment_status='UNASSIGNED').count()
            stats['my_voyages'] = my_voyages.count()
            stats['unassigned_voyages'] = unassigned_voyages
        else:
            stats['my_voyages'] = 0
            stats['unassigned_voyages'] = 0

        # Recent claims
        recent_claims = my_claims_queryset.order_by('-created_at')[:10]

        context.update({
            'stats': stats,
            'recent_claims': recent_claims,
        })

        return context


# ============================================================================
# CLAIM VIEWS
# ============================================================================

class ClaimListView(LoginRequiredMixin, ListView):
    """List all claims with filtering"""
    model = Claim
    template_name = 'claims/claim_list.html'
    context_object_name = 'claims'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        queryset = Claim.objects.select_related(
            'voyage', 'ship_owner', 'assigned_to', 'created_by'
        ).order_by('-created_at')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by payment status
        payment_status = self.request.GET.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        # Filter by ship owner
        ship_owner_id = self.request.GET.get('ship_owner')
        if ship_owner_id:
            queryset = queryset.filter(ship_owner_id=ship_owner_id)

        # Filter by assigned analyst
        assigned_to_id = self.request.GET.get('assigned_to')
        if assigned_to_id:
            queryset = queryset.filter(assigned_to_id=assigned_to_id)

        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(claim_number__icontains=search_query) |
                Q(voyage__voyage_number__icontains=search_query) |
                Q(voyage__vessel_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['ship_owners'] = ShipOwner.objects.filter(is_active=True).order_by('name')
        context['analysts'] = User.objects.filter(role__in=['WRITE', 'TEAM_LEAD', 'ADMIN'])
        return context


class ClaimDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single claim"""
    model = Claim
    template_name = 'claims/claim_detail.html'
    context_object_name = 'claim'

    def get_queryset(self) -> QuerySet:
        return Claim.objects.select_related(
            'voyage', 'ship_owner', 'assigned_to', 'created_by'
        ).prefetch_related('comments__user', 'documents', 'activity_logs')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        claim = self.object

        context.update({
            'comments': claim.comments.all().order_by('created_at'),
            'documents': claim.documents.all().order_by('-uploaded_at'),
            'activity_logs': claim.activity_logs.all().order_by('-created_at')[:20],
            'comment_form': CommentForm(),
            'document_form': DocumentForm(),
            'can_edit': claim.can_edit(self.request.user),
            'can_delete': claim.can_delete(self.request.user),
        })

        return context


class ClaimCreateView(LoginRequiredMixin, CanWriteMixin, CreateView):
    """Create a new claim"""
    model = Claim
    form_class = ClaimForm
    template_name = 'claims/claim_form.html'
    success_url = reverse_lazy('claim_list')

    def form_valid(self, form: ClaimForm) -> HttpResponse:
        form.instance.created_by = self.request.user

        # Auto-assign to voyage analyst if not assigned
        if not form.instance.assigned_to and form.instance.voyage:
            form.instance.assigned_to = form.instance.voyage.assigned_analyst

        response = super().form_valid(form)

        # Log activity
        ClaimActivityLog.objects.create(
            claim=self.object,
            claim_number=self.object.claim_number,
            user=self.request.user,
            action='CREATED',
            message=f'Claim created by {self.request.user.get_full_name()}'
        )

        messages.success(self.request, f'Claim {self.object.claim_number} created successfully!')
        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Claim'
        return context


class ClaimUpdateView(LoginRequiredMixin, CanWriteMixin, UpdateView):
    """Update an existing claim"""
    model = Claim
    form_class = ClaimForm
    template_name = 'claims/claim_form.html'

    def get_success_url(self) -> str:
        return reverse_lazy('claim_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form: ClaimForm) -> HttpResponse:
        # Track changes for activity log
        if form.has_changed():
            old_instance = Claim.objects.get(pk=self.object.pk)

            # Log specific important changes
            if 'status' in form.changed_data:
                ClaimActivityLog.objects.create(
                    claim=self.object,
                    claim_number=self.object.claim_number,
                    user=self.request.user,
                    action='STATUS_CHANGED',
                    message=f'Status changed from {old_instance.get_status_display()} to {self.object.get_status_display()}',
                    old_value=old_instance.status,
                    new_value=self.object.status
                )

            if 'claim_amount' in form.changed_data:
                ClaimActivityLog.objects.create(
                    claim=self.object,
                    claim_number=self.object.claim_number,
                    user=self.request.user,
                    action='AMOUNT_CHANGED',
                    message=f'Claim amount changed from ${old_instance.claim_amount:,.2f} to ${self.object.claim_amount:,.2f}',
                    old_value=str(old_instance.claim_amount),
                    new_value=str(self.object.claim_amount)
                )

        messages.success(self.request, f'Claim {self.object.claim_number} updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Claim {self.object.claim_number}'
        return context


class ClaimDeleteView(LoginRequiredMixin, CanWriteMixin, DeleteView):
    """Delete a claim"""
    model = Claim
    template_name = 'claims/claim_confirm_delete.html'
    success_url = reverse_lazy('claim_list')

    def test_func(self) -> bool:
        """Only allow deletion if user has permission"""
        claim = self.get_object()
        return claim.can_delete(self.request.user)

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        claim = self.get_object()
        claim_number = claim.claim_number

        # Log deletion before actual delete
        ClaimActivityLog.objects.create(
            claim=None,  # Claim will be deleted
            claim_number=claim_number,
            user=request.user,
            action='DELETED',
            message=f'Claim deleted by {request.user.get_full_name()}'
        )

        messages.success(request, f'Claim {claim_number} deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# VOYAGE VIEWS
# ============================================================================

class VoyageListView(LoginRequiredMixin, ListView):
    """List all voyages with filtering"""
    model = Voyage
    template_name = 'claims/voyage_list.html'
    context_object_name = 'voyages'
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        queryset = Voyage.objects.select_related(
            'ship_owner', 'assigned_analyst'
        ).annotate(
            claims_count=Count('claims')
        ).order_by('-created_at')

        # Filter by assignment status
        assignment_status = self.request.GET.get('assignment_status')
        if assignment_status:
            queryset = queryset.filter(assignment_status=assignment_status)

        # Filter by charter type
        charter_type = self.request.GET.get('charter_type')
        if charter_type:
            queryset = queryset.filter(charter_type=charter_type)

        # Filter by ship owner
        ship_owner_id = self.request.GET.get('ship_owner')
        if ship_owner_id:
            queryset = queryset.filter(ship_owner_id=ship_owner_id)

        # Filter by assigned analyst
        assigned_analyst_id = self.request.GET.get('assigned_analyst')
        if assigned_analyst_id:
            queryset = queryset.filter(assigned_analyst_id=assigned_analyst_id)

        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(voyage_number__icontains=search_query) |
                Q(vessel_name__icontains=search_query) |
                Q(imo_number__icontains=search_query) |
                Q(charter_party__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['ship_owners'] = ShipOwner.objects.filter(is_active=True).order_by('name')
        context['analysts'] = User.objects.filter(role__in=['WRITE', 'TEAM_LEAD', 'ADMIN'])
        return context


class VoyageDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single voyage"""
    model = Voyage
    template_name = 'claims/voyage_detail.html'
    context_object_name = 'voyage'

    def get_queryset(self) -> QuerySet:
        return Voyage.objects.select_related(
            'ship_owner', 'assigned_analyst'
        ).prefetch_related('claims', 'assignment_history')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        voyage = self.object

        context.update({
            'claims': voyage.claims.all().order_by('-created_at'),
            'assignment_history': voyage.assignment_history.all().order_by('-assigned_at'),
            'can_assign': self.request.user.can_assign_voyages(),
            'analysts': User.objects.filter(role__in=['WRITE', 'TEAM_LEAD', 'ADMIN']),
        })

        return context


# ============================================================================
# SHIP OWNER VIEWS
# ============================================================================

class ShipOwnerListView(LoginRequiredMixin, ListView):
    """List all ship owners"""
    model = ShipOwner
    template_name = 'claims/ship_owner_list.html'
    context_object_name = 'ship_owners'
    paginate_by = 50

    def get_queryset(self) -> QuerySet:
        queryset = ShipOwner.objects.annotate(
            voyages_count=Count('voyages'),
            claims_count=Count('claims')
        ).order_by('name')

        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=(is_active == 'true'))

        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(code__icontains=search_query) |
                Q(contact_email__icontains=search_query)
            )

        return queryset


class ShipOwnerDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a ship owner"""
    model = ShipOwner
    template_name = 'claims/ship_owner_detail.html'
    context_object_name = 'ship_owner'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        ship_owner = self.object

        # Get voyages and claims
        voyages = ship_owner.voyages.all().order_by('-laycan_start')[:10]
        claims = ship_owner.claims.select_related('voyage').order_by('-created_at')[:10]

        # Calculate statistics
        total_claim_amount = ship_owner.claims.aggregate(
            total=Sum('claim_amount')
        )['total'] or 0

        total_paid = ship_owner.claims.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0

        context.update({
            'voyages': voyages,
            'claims': claims,
            'total_voyages': ship_owner.voyages.count(),
            'total_claims': ship_owner.claims.count(),
            'total_claim_amount': total_claim_amount,
            'total_paid': total_paid,
            'outstanding': total_claim_amount - total_paid,
        })

        return context
