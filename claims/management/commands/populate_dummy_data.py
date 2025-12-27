from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from claims.models import User, Claim, Comment, Document


class Command(BaseCommand):
    help = 'Populates the database with dummy data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating users...')

        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'ADMIN',
                'department': 'Management',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: admin/admin123'))

        # Create analysts
        analysts = []
        analyst_data = [
            {'username': 'john.smith', 'first_name': 'John', 'last_name': 'Smith', 'role': 'WRITE', 'department': 'Claims Department'},
            {'username': 'jane.doe', 'first_name': 'Jane', 'last_name': 'Doe', 'role': 'WRITE', 'department': 'Claims Department'},
            {'username': 'bob.wilson', 'first_name': 'Bob', 'last_name': 'Wilson', 'role': 'READ_EXPORT', 'department': 'Finance'},
            {'username': 'alice.brown', 'first_name': 'Alice', 'last_name': 'Brown', 'role': 'READ', 'department': 'Operations'},
        ]

        for data in analyst_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': f"{data['username']}@example.com",
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': data['role'],
                    'department': data['department'],
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {data['username']}/password123"))
            analysts.append(user)

        self.stdout.write('Creating claims...')

        # Sample vessel and port data
        vessels = [
            'MV Pacific Star', 'MV Atlantic Dawn', 'MV Ocean Explorer',
            'MV Northern Light', 'MV Southern Cross', 'MV Eastern Pearl'
        ]

        ports = [
            ('Singapore', 'Rotterdam'),
            ('Shanghai', 'Hamburg'),
            ('Houston', 'Tokyo'),
            ('Dubai', 'New York'),
            ('Santos', 'Antwerp'),
        ]

        statuses = ['DRAFT', 'UNDER_REVIEW', 'SUBMITTED', 'SETTLED', 'REJECTED']
        claim_types = ['DEMURRAGE', 'POST_DEAL', 'OTHER']

        claims = []
        for i in range(15):
            load_port, discharge_port = ports[i % len(ports)]
            vessel = vessels[i % len(vessels)]

            laycan_start = timezone.now().date() - timedelta(days=60 - i * 3)
            laycan_end = laycan_start + timedelta(days=5)

            laytime_allowed = Decimal(str(5 + (i % 3)))
            laytime_used = Decimal(str(laytime_allowed + 2 + (i % 4)))
            demurrage_rate = Decimal(str(10000 + (i * 500)))
            demurrage_days = max(Decimal('0'), laytime_used - laytime_allowed)
            claim_amount = demurrage_days * demurrage_rate

            claim = Claim.objects.create(
                claim_type=claim_types[i % len(claim_types)],
                status=statuses[i % len(statuses)],
                voyage_number=f'V{2024001 + i}',
                vessel_name=vessel,
                charter_party=f'CP-{2024001 + i}',
                load_port=load_port,
                discharge_port=discharge_port,
                laycan_start=laycan_start,
                laycan_end=laycan_end,
                demurrage_rate=demurrage_rate,
                laytime_allowed=laytime_allowed,
                laytime_used=laytime_used,
                claim_amount=claim_amount,
                currency='USD',
                description=f'Demurrage claim for voyage {vessel} from {load_port} to {discharge_port}. '
                           f'Vessel exceeded allowed laytime by {demurrage_days} days.',
                created_by=analysts[i % len(analysts)],
                assigned_to=analysts[(i + 1) % len(analysts)] if i % 2 == 0 else None,
            )

            # Set timestamps based on status
            if claim.status in ['SUBMITTED', 'SETTLED', 'REJECTED']:
                claim.submitted_at = timezone.now() - timedelta(days=30 - i)
                if claim.status in ['SETTLED', 'REJECTED']:
                    claim.settled_at = timezone.now() - timedelta(days=10 - i % 10)
                    claim.settlement_notes = f'Claim was {claim.status.lower()} after review.'
                claim.save()

            claims.append(claim)
            self.stdout.write(f'Created claim: {claim.claim_number}')

        self.stdout.write('Creating comments...')

        # Add comments to some claims
        for i, claim in enumerate(claims[:10]):
            Comment.objects.create(
                claim=claim,
                user=analysts[i % len(analysts)],
                content=f'Initial review completed. Documentation looks good.',
            )

            if i % 2 == 0:
                Comment.objects.create(
                    claim=claim,
                    user=analysts[(i + 1) % len(analysts)],
                    content=f'Approved for submission. Please proceed with filing.',
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated dummy data!'))
        self.stdout.write('')
        self.stdout.write('Test Users Created:')
        self.stdout.write('  admin/admin123 (Admin)')
        self.stdout.write('  john.smith/password123 (Write)')
        self.stdout.write('  jane.doe/password123 (Write)')
        self.stdout.write('  bob.wilson/password123 (Read+Export)')
        self.stdout.write('  alice.brown/password123 (Read Only)')
        self.stdout.write('')
        self.stdout.write(f'Created {len(claims)} claims with various statuses')
