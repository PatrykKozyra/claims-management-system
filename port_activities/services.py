"""
Business logic and services for port activities.
Provides functions for querying and filtering port activities.
"""

from django.db.models import Q, Sum, Count, Avg, F
from .models import PortActivity, ActivityType


class PortActivityService:
    """Business logic for port activities"""

    @staticmethod
    def get_ship_timeline(ship_id, start_date=None, end_date=None):
        """
        Get all activities for a ship in date range.

        Args:
            ship_id: Ship primary key
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            QuerySet of PortActivity objects
        """
        qs = PortActivity.objects.filter(ship_id=ship_id).select_related(
            'activity_type', 'voyage', 'created_by', 'ship'
        )

        if start_date:
            qs = qs.filter(start_datetime__gte=start_date)
        if end_date:
            qs = qs.filter(end_datetime__lte=end_date)

        return qs.order_by('start_datetime')

    @staticmethod
    def get_voyage_activities(voyage_id):
        """
        Get all activities for a specific voyage.

        Args:
            voyage_id: Voyage primary key

        Returns:
            QuerySet of PortActivity objects
        """
        return PortActivity.objects.filter(
            voyage_id=voyage_id
        ).select_related(
            'activity_type', 'ship', 'created_by'
        ).order_by('start_datetime')

    @staticmethod
    def filter_by_activity_category(category, start_date=None, end_date=None):
        """
        Get all activities of a specific category (STS, DRYDOCK, OFFHIRE, etc.).

        Args:
            category: Activity category from ActivityType.CATEGORY_CHOICES
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            QuerySet of PortActivity objects
        """
        qs = PortActivity.objects.filter(
            activity_type__category=category
        ).select_related('ship', 'voyage', 'activity_type', 'created_by')

        if start_date:
            qs = qs.filter(start_datetime__gte=start_date)
        if end_date:
            qs = qs.filter(end_datetime__lte=end_date)

        return qs.order_by('-start_datetime')

    @staticmethod
    def get_sts_operations(start_date=None, end_date=None):
        """Get all Ship-to-Ship transfer operations"""
        return PortActivityService.filter_by_activity_category(
            'STS', start_date, end_date
        )

    @staticmethod
    def get_drydock_operations(start_date=None, end_date=None):
        """Get all dry-docking operations"""
        return PortActivityService.filter_by_activity_category(
            'DRYDOCK', start_date, end_date
        )

    @staticmethod
    def get_offhire_periods(start_date=None, end_date=None):
        """Get all off-hire periods"""
        return PortActivityService.filter_by_activity_category(
            'OFFHIRE', start_date, end_date
        )

    @staticmethod
    def get_pivot_data(filters=None):
        """
        Get hierarchical data: Ship → Voyage → Activities.
        For pivot table display.

        Args:
            filters: Dict with optional filters:
                - ship_id: Filter by specific ship
                - activity_category: Filter by activity category
                - start_date: Filter activities starting after this date
                - end_date: Filter activities ending before this date
                - voyage_id: Filter by specific voyage
                - date_status: Filter by 'ESTIMATED' or 'ACTUAL'

        Returns:
            Dict with structure: {ship_name: {voyage_number: [activities]}}
        """
        from ships.models import Ship
        from claims.models import Voyage

        # Start with all activities
        activities_qs = PortActivity.objects.all().select_related(
            'ship', 'voyage', 'activity_type', 'created_by'
        )

        # Apply filters if provided
        if filters:
            if filters.get('ship_id'):
                activities_qs = activities_qs.filter(ship_id=filters['ship_id'])

            if filters.get('activity_category'):
                activities_qs = activities_qs.filter(
                    activity_type__category=filters['activity_category']
                )

            if filters.get('start_date'):
                activities_qs = activities_qs.filter(
                    start_datetime__gte=filters['start_date']
                )

            if filters.get('end_date'):
                activities_qs = activities_qs.filter(
                    end_datetime__lte=filters['end_date']
                )

            if filters.get('voyage_id'):
                activities_qs = activities_qs.filter(voyage_id=filters['voyage_id'])

            if filters.get('date_status'):
                # Filter by estimated or actual dates
                status = filters['date_status']
                activities_qs = activities_qs.filter(
                    Q(start_date_status=status) | Q(end_date_status=status)
                )

        # Group by ship, then voyage
        pivot_data = {}
        for activity in activities_qs.order_by('ship', 'voyage', 'start_datetime'):
            ship_name = activity.ship.vessel_name
            voyage_number = activity.voyage.voyage_number if activity.voyage else 'No Voyage'

            if ship_name not in pivot_data:
                pivot_data[ship_name] = {}

            if voyage_number not in pivot_data[ship_name]:
                pivot_data[ship_name][voyage_number] = []

            pivot_data[ship_name][voyage_number].append(activity)

        return pivot_data

    @staticmethod
    def get_activity_summary_by_ship(start_date=None, end_date=None):
        """
        Get summary statistics of activities grouped by ship.

        Returns:
            QuerySet with aggregated data
        """
        qs = PortActivity.objects.select_related('ship', 'activity_type')

        if start_date:
            qs = qs.filter(start_datetime__gte=start_date)
        if end_date:
            qs = qs.filter(end_datetime__lte=end_date)

        return qs.values(
            'ship__vessel_name', 'ship__imo_number'
        ).annotate(
            total_activities=Count('id'),
            total_cargo=Sum('cargo_quantity'),
            avg_duration_days=Avg(F('duration'))
        ).order_by('-total_activities')

    @staticmethod
    def get_activity_summary_by_type(start_date=None, end_date=None):
        """
        Get summary statistics of activities grouped by activity type.

        Returns:
            QuerySet with aggregated data
        """
        qs = PortActivity.objects.select_related('activity_type')

        if start_date:
            qs = qs.filter(start_datetime__gte=start_date)
        if end_date:
            qs = qs.filter(end_datetime__lte=end_date)

        return qs.values(
            'activity_type__name', 'activity_type__category'
        ).annotate(
            total_activities=Count('id'),
            total_cargo=Sum('cargo_quantity'),
        ).order_by('activity_type__category', 'activity_type__name')
