"""
Notification Service

This service handles all notifications (email, in-app, etc.)
"""
from typing import List, Dict, Any, Optional
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service class for sending notifications"""

    def __init__(self):
        """Initialize notification service"""
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@claims-system.com')

    def send_email(
        self,
        subject: str,
        message: str,
        recipient_list: List[str],
        html_message: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send email notification

        Args:
            subject: Email subject
            message: Plain text message
            recipient_list: List of recipient email addresses
            html_message: Optional HTML version of message
            from_email: Optional from email address

        Returns:
            bool: True if email sent successfully
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email or self.from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email sent to {len(recipient_list)} recipients: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_claim_submitted_notification(self, claim, recipient_list: List[str]) -> bool:
        """
        Send notification when a claim is submitted

        Args:
            claim: Claim object
            recipient_list: List of recipient emails

        Returns:
            bool: Success status
        """
        subject = f"Claim Submitted: {claim.claim_number}"

        message = f"""
        A new claim has been submitted.

        Claim Number: {claim.claim_number}
        Type: {claim.get_claim_type_display()}
        Amount: ${claim.claim_amount:,.2f}
        Voyage: {claim.voyage.voyage_number}
        Vessel: {claim.voyage.vessel_name}
        Assigned To: {claim.assigned_to.get_full_name() if claim.assigned_to else 'Unassigned'}

        Please log in to review the claim.
        """

        return self.send_email(subject, message, recipient_list)

    def send_claim_assigned_notification(self, claim, recipient_list: List[str]) -> bool:
        """
        Send notification when a claim is assigned

        Args:
            claim: Claim object
            recipient_list: List of recipient emails

        Returns:
            bool: Success status
        """
        subject = f"Claim Assigned to You: {claim.claim_number}"

        message = f"""
        You have been assigned a new claim.

        Claim Number: {claim.claim_number}
        Type: {claim.get_claim_type_display()}
        Amount: ${claim.claim_amount:,.2f}
        Voyage: {claim.voyage.voyage_number}
        Vessel: {claim.voyage.vessel_name}
        Status: {claim.get_status_display()}
        Deadline: {claim.claim_deadline.strftime('%Y-%m-%d') if claim.claim_deadline else 'Not set'}

        Please log in to view the claim details.
        """

        return self.send_email(subject, message, recipient_list)

    def send_timebar_warning_notification(self, claim, days_remaining: int, recipient_list: List[str]) -> bool:
        """
        Send warning when claim is approaching time-bar

        Args:
            claim: Claim object
            days_remaining: Days until time-bar
            recipient_list: List of recipient emails

        Returns:
            bool: Success status
        """
        subject = f"⚠️ Time-Bar Warning: {claim.claim_number} ({days_remaining} days)"

        message = f"""
        WARNING: Claim is approaching time-bar deadline!

        Claim Number: {claim.claim_number}
        Amount: ${claim.claim_amount:,.2f}
        Voyage: {claim.voyage.voyage_number}
        Vessel: {claim.voyage.vessel_name}
        Deadline: {claim.claim_deadline.strftime('%Y-%m-%d')}
        Days Remaining: {days_remaining}

        URGENT ACTION REQUIRED: Please submit this claim before the deadline.
        """

        return self.send_email(subject, message, recipient_list)

    def send_payment_received_notification(self, claim, amount, recipient_list: List[str]) -> bool:
        """
        Send notification when payment is received

        Args:
            claim: Claim object
            amount: Payment amount
            recipient_list: List of recipient emails

        Returns:
            bool: Success status
        """
        subject = f"Payment Received: {claim.claim_number}"

        message = f"""
        A payment has been received for claim {claim.claim_number}.

        Claim Number: {claim.claim_number}
        Payment Amount: ${amount:,.2f}
        Total Paid: ${claim.paid_amount:,.2f}
        Outstanding: ${claim.outstanding_amount:,.2f}
        Payment Status: {claim.get_payment_status_display()}

        View full claim details in the system.
        """

        return self.send_email(subject, message, recipient_list)

    def send_voyage_assigned_notification(self, voyage, recipient_list: List[str]) -> bool:
        """
        Send notification when voyage is assigned

        Args:
            voyage: Voyage object
            recipient_list: List of recipient emails

        Returns:
            bool: Success status
        """
        subject = f"Voyage Assigned to You: {voyage.voyage_number}"

        message = f"""
        You have been assigned a new voyage.

        Voyage Number: {voyage.voyage_number}
        Vessel: {voyage.vessel_name}
        Charter Party: {voyage.charter_party}
        Load Port: {voyage.load_port}
        Discharge Port: {voyage.discharge_port}
        Laycan: {voyage.laycan_start.strftime('%Y-%m-%d')} to {voyage.laycan_end.strftime('%Y-%m-%d')}

        Please review the voyage details and monitor for any claims.
        """

        return self.send_email(subject, message, recipient_list)

    def send_export_ready_notification(self, user, file_path: str, export_type: str) -> bool:
        """
        Send notification when export is ready

        Args:
            user: User who requested export
            file_path: Path to exported file
            export_type: Type of export

        Returns:
            bool: Success status
        """
        if not user.email:
            return False

        subject = f"✅ Your {export_type.title()} Export is Ready"

        message = f"""
        Dear {user.get_full_name()},

        Your requested {export_type} export has been completed and is ready for download.

        File: {file_path}

        Please log in to the Claims Management System to download your file.

        Best regards,
        Claims Management System
        """

        return self.send_email(subject, message, [user.email])

    def send_daily_summary(self, user, summary_data: Dict[str, Any]) -> bool:
        """
        Send daily summary email to user

        Args:
            user: User to send summary to
            summary_data: Dictionary with summary statistics

        Returns:
            bool: Success status
        """
        if not user.email:
            return False

        subject = f"📊 Daily Summary - {summary_data.get('date', '')}"

        message = f"""
        Daily Summary for {summary_data.get('date', '')}

        Voyages:
        - Total: {summary_data.get('total_voyages', 0)}
        - Assigned to you: {summary_data.get('your_voyages', 0)}

        Claims:
        - Total: {summary_data.get('total_claims', 0)}
        - Assigned to you: {summary_data.get('your_claims', 0)}
        - Pending: {summary_data.get('pending_claims', 0)}
        - Approaching time-bar: {summary_data.get('timebar_warnings', 0)}

        Total Outstanding Amount: ${summary_data.get('outstanding_amount', 0):,.2f}

        Log in to view detailed reports.
        """

        return self.send_email(subject, message, [user.email])

    def send_bulk_notification(
        self,
        subject: str,
        message: str,
        user_queryset,
        filter_condition: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Send notification to multiple users

        Args:
            subject: Email subject
            message: Email message
            user_queryset: QuerySet of users
            filter_condition: Optional function to filter users

        Returns:
            dict: Results with success/failure counts
        """
        success_count = 0
        failed_count = 0
        recipients = []

        for user in user_queryset:
            if filter_condition and not filter_condition(user):
                continue

            if user.email:
                recipients.append(user.email)

        if recipients:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=recipients,
                    fail_silently=False,
                )
                success_count = len(recipients)
                logger.info(f"Bulk notification sent to {success_count} users")

            except Exception as e:
                failed_count = len(recipients)
                logger.error(f"Bulk notification failed: {e}")

        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(recipients)
        }
