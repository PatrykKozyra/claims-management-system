from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from claims.models import User, Claim, Comment, Document, Voyage, ShipOwner


class Command(BaseCommand):
    help = 'Simulates RADAR system importing voyage and claims data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--voyages',
            type=int,
            default=30,
            help='Number of voyages to create (default: 30)'
        )

    def handle(self, *args, **kwargs):
        num_voyages = kwargs['voyages']

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('RADAR DATA IMPORT SIMULATION'))
        self.stdout.write('=' * 60)

        # Create users if they don't exist
        self.stdout.write('\n1. Creating users...')
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@company.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'ADMIN',
                'department': 'Management',
                'position': 'System Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'   [Created] Admin user')
        else:
            self.stdout.write(f'   [Exists] Admin user')

        # Create Team Lead
        team_lead, created = User.objects.get_or_create(
            username='sarah.teamlead',
            defaults={
                'email': 'sarah@company.com',
                'first_name': 'Sarah',
                'last_name': 'Williams',
                'position': 'Team Lead - Claims',
                'department': 'Claims Department',
                'role': 'TEAM_LEAD',
                'created_by': admin,
            }
        )
        if created:
            team_lead.set_password('password123')
            team_lead.save()
            self.stdout.write(f'   [Created] {team_lead.username} (Team Lead)')
        else:
            self.stdout.write(f'   [Exists] {team_lead.username} (Team Lead)')

        analysts_data = [
            {'username': 'john.analyst', 'first_name': 'John', 'last_name': 'Smith', 'email': 'john@company.com', 'position': 'Senior Claims Analyst', 'department': 'Claims Department'},
            {'username': 'jane.analyst', 'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane@company.com', 'position': 'Claims Analyst', 'department': 'Claims Department'},
            {'username': 'mike.analyst', 'first_name': 'Mike', 'last_name': 'Johnson', 'email': 'mike@company.com', 'position': 'Junior Claims Analyst', 'department': 'Claims Department'},
        ]

        analysts = []
        for data in analysts_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'position': data['position'],
                    'department': data['department'],
                    'role': 'WRITE',
                    'created_by': admin,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'   [Created] {user.username}')
            else:
                self.stdout.write(f'   [Exists] {user.username}')
            analysts.append(user)

        # Create Ship Owners
        self.stdout.write('\n2. Creating ship owners...')
        ship_owners_data = [
            {'name': 'Maersk Line', 'code': 'MAERSK'},
            {'name': 'MSC Mediterranean Shipping', 'code': 'MSC'},
            {'name': 'CMA CGM Group', 'code': 'CMACGM'},
            {'name': 'COSCO Shipping Lines', 'code': 'COSCO'},
            {'name': 'Hapag-Lloyd', 'code': 'HAPAG'},
            {'name': 'ONE (Ocean Network Express)', 'code': 'ONE'},
            {'name': 'Evergreen Marine', 'code': 'EVERGRN'},
            {'name': 'Yang Ming Marine Transport', 'code': 'YANGMING'},
        ]

        ship_owners = []
        for owner_data in ship_owners_data:
            owner, created = ShipOwner.objects.get_or_create(
                code=owner_data['code'],
                defaults={
                    'name': owner_data['name'],
                    'contact_email': f'claims@{owner_data["code"].lower()}.com',
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'   [Created] {owner.name}')
            else:
                self.stdout.write(f'   [Exists] {owner.name}')
            ship_owners.append(owner)

        # Create Voyages
        self.stdout.write(f'\n3. Creating {num_voyages} voyages...')
        vessel_names = [
            'MV Pacific Glory', 'MV Atlantic Star', 'MV Ocean Explorer',
            'MV Neptune Voyager', 'MV Seahawk', 'MV Marine Explorer',
            'MV Blue Ocean', 'MV Golden Wave', 'MV Silver Dolphin',
            'MV Eastern Pride', 'MV Western Fortune', 'MV Northern Light',
            'MV Southern Cross', 'MV Coral Princess', 'MV Pearl Navigator',
            'MV Diamond Trader', 'MV Emerald Explorer', 'MV Ruby Carrier',
            'MV Sapphire Voyager', 'MV Topaz Trader', 'MV Crystal Wave',
            'MV Phoenix Rising', 'MV Thunder Bay', 'MV Lightning Star',
            'MV Storm Chaser', 'MV Wind Runner', 'MV Sea Pioneer',
            'MV Ocean Majesty', 'MV Neptune Queen', 'MV Atlantic Breeze',
        ]

        ports = [
            ('Shanghai', 'Rotterdam'), ('Singapore', 'Hamburg'), ('Hong Kong', 'Los Angeles'),
            ('Dubai', 'Southampton'), ('Mumbai', 'Antwerp'), ('Tokyo', 'Long Beach'),
            ('Busan', 'Felixstowe'), ('Port Klang', 'New York'), ('Guangzhou', 'Vancouver'),
            ('Qingdao', 'Savannah'), ('Ningbo', 'Oakland'), ('Shenzhen', 'Seattle'),
        ]

        charter_parties = ['GENCON', 'NYPE', 'BALTIME', 'SHELLVOY', 'EXXONVOY']

        voyages_created = 0
        for i in range(num_voyages):
            load_port, discharge_port = random.choice(ports)
            voyage_number = f'V{timezone.now().year}{str(10000 + i + Voyage.objects.count()).zfill(5)}'
            radar_voyage_id = f'RADAR-V-{timezone.now().year}-{10000 + i + Voyage.objects.count()}'

            # Random assignment: 30% unassigned, 70% assigned
            is_assigned = random.random() > 0.3
            assigned_analyst = random.choice(analysts) if is_assigned else None
            assignment_status = 'ASSIGNED' if is_assigned else 'UNASSIGNED'

            laycan_start = timezone.now().date() + timedelta(days=random.randint(-30, 60))
            laycan_end = laycan_start + timedelta(days=random.randint(3, 7))

            voyage, created = Voyage.objects.get_or_create(
                radar_voyage_id=radar_voyage_id,
                defaults={
                    'voyage_number': voyage_number,
                    'vessel_name': random.choice(vessel_names),
                    'imo_number': f'IMO{random.randint(1000000, 9999999)}',
                    'charter_party': random.choice(charter_parties),
                    'load_port': load_port,
                    'discharge_port': discharge_port,
                    'laycan_start': laycan_start,
                    'laycan_end': laycan_end,
                    'ship_owner': random.choice(ship_owners),
                    'demurrage_rate': Decimal(random.uniform(5000, 25000)).quantize(Decimal('0.01')),
                    
                    'laytime_allowed': Decimal(random.uniform(48, 168)).quantize(Decimal('0.01')),
                    'currency': 'USD',
                    'assignment_status': assignment_status,
                    'assigned_analyst': assigned_analyst,
                    'assigned_at': timezone.now() if is_assigned else None,
                    
                }
            )

            if created:
                voyages_created += 1
                status_icon = '[ASSIGNED]' if is_assigned else '[UNASSIGNED]'
                analyst_name = assigned_analyst.get_full_name() if assigned_analyst else 'None'
                self.stdout.write(f'   {status_icon} {voyage.voyage_number} - {voyage.vessel_name} (Analyst: {analyst_name})')

                # Create claims for this voyage
                # Always create 1 Demurrage claim
                demurrage_claim = self.create_demurrage_claim(voyage, assigned_analyst, admin)
                self.stdout.write(f'      + Demurrage claim: {demurrage_claim.claim_number}')

                # Create 1-4 Post-Deal claims
                num_post_deal = random.randint(1, 4)
                cost_types = ['PORT_CHARGES', 'DEVIATION_COSTS', 'CLEANING_COSTS', 'OTHER_COSTS']
                for j in range(num_post_deal):
                    cost_type = cost_types[j % len(cost_types)]
                    post_deal_claim = self.create_post_deal_claim(voyage, cost_type, assigned_analyst, admin)
                    self.stdout.write(f'      + Post-Deal claim ({cost_type}): {post_deal_claim.claim_number}')

                # Randomly create Despatch claim (20% chance)
                if random.random() < 0.2:
                    despatch_claim = self.create_despatch_claim(voyage, assigned_analyst, admin)
                    self.stdout.write(f'      + Despatch claim: {despatch_claim.claim_number}')

        self.stdout.write(f'\n   Created {voyages_created} new voyages')

        # Add some comments to claims
        self.stdout.write('\n4. Adding analyst comments...')
        claims_with_comments = Claim.objects.filter(assigned_to__isnull=False).order_by('?')[:10]
        comment_templates = [
            "Contacted ship owner regarding this claim.",
            "Awaiting response from charterer.",
            "Documents received and under review.",
            "Sent claim to ship owner for payment.",
            "Negotiating settlement amount.",
            "Payment partially received, following up on balance.",
            "Claim approved by manager, proceeding with submission.",
        ]

        for claim in claims_with_comments:
            Comment.objects.get_or_create(
                claim=claim,
                user=claim.assigned_to,
                defaults={'content': random.choice(comment_templates)}
            )
        self.stdout.write(f'   Added {len(claims_with_comments)} comments')

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('SIMULATION COMPLETE'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'\nUsers: {User.objects.count()}')
        self.stdout.write(f'Ship Owners: {ShipOwner.objects.count()}')
        self.stdout.write(f'Voyages: {Voyage.objects.count()}')
        self.stdout.write(f'Claims: {Claim.objects.count()}')
        self.stdout.write(f'Comments: {Comment.objects.count()}')
        self.stdout.write('\nYou can now login with:')
        self.stdout.write('  admin / admin123 (Administrator)')
        self.stdout.write('  sarah.teamlead / password123 (Team Lead)')
        self.stdout.write('  john.analyst / password123 (Senior Analyst)')
        self.stdout.write('  jane.analyst / password123 (Analyst)')
        self.stdout.write('  mike.analyst / password123 (Junior Analyst)')
        self.stdout.write('\nServer: http://127.0.0.1:8001/')

    def create_demurrage_claim(self, voyage, assigned_analyst, created_by):
        """Create a demurrage claim for the voyage"""
        laytime_used = float(voyage.laytime_allowed) + random.uniform(10, 100)
        demurrage_days = (laytime_used - float(voyage.laytime_allowed)) / 24
        claim_amount = demurrage_days * float(voyage.demurrage_rate)

        payment_statuses = ['NOT_SENT', 'SENT', 'SENT', 'PARTIALLY_PAID', 'PAID', 'PAID']
        payment_status = random.choice(payment_statuses)

        # 10% chance of being time-barred
        is_time_barred = random.random() < 0.1

        if is_time_barred:
            payment_status = 'TIMEBAR'
            claim_deadline = timezone.now().date() - timedelta(days=random.randint(1, 30))
        else:
            claim_deadline = timezone.now().date() + timedelta(days=random.randint(30, 180))

        # Payment amounts
        if payment_status == 'PAID':
            paid_amount = claim_amount
        elif payment_status == 'PARTIALLY_PAID':
            paid_amount = claim_amount * random.uniform(0.3, 0.8)
        else:
            paid_amount = 0

        claim = Claim.objects.create(
            voyage=voyage,
            ship_owner=voyage.ship_owner,
            claim_type='DEMURRAGE',
            status=random.choice(['DRAFT', 'UNDER_REVIEW', 'SUBMITTED', 'SETTLED']),
            payment_status=payment_status,
            laytime_used=Decimal(laytime_used).quantize(Decimal('0.01')),
            claim_amount=Decimal(claim_amount).quantize(Decimal('0.01')),
            paid_amount=Decimal(paid_amount).quantize(Decimal('0.01')),
            currency=voyage.currency,
            claim_deadline=claim_deadline,
            is_time_barred=is_time_barred,
            time_bar_date=claim_deadline if is_time_barred else None,
            description=f'Demurrage claim for voyage {voyage.voyage_number}. Laytime exceeded by {demurrage_days:.2f} days.',
            assigned_to=assigned_analyst,
            created_by=created_by,
        )
        return claim

    def create_post_deal_claim(self, voyage, cost_type, assigned_analyst, created_by):
        """Create a post-deal claim for the voyage"""
        claim_amount = random.uniform(5000, 50000)
        payment_statuses = ['NOT_SENT', 'SENT', 'PARTIALLY_PAID', 'PAID']
        payment_status = random.choice(payment_statuses)

        claim_deadline = timezone.now().date() + timedelta(days=random.randint(30, 180))

        if payment_status == 'PAID':
            paid_amount = claim_amount
        elif payment_status == 'PARTIALLY_PAID':
            paid_amount = claim_amount * random.uniform(0.4, 0.9)
        else:
            paid_amount = 0

        descriptions = {
            'PORT_CHARGES': f'Port charges incurred at {voyage.discharge_port}',
            'DEVIATION_COSTS': f'Deviation costs from {voyage.load_port} to {voyage.discharge_port}',
            'CLEANING_COSTS': 'Tank cleaning and preparation costs',
            'OTHER_COSTS': 'Additional operational costs',
        }

        claim = Claim.objects.create(
            voyage=voyage,
            ship_owner=voyage.ship_owner,
            claim_type='POST_DEAL',
            cost_type=cost_type,
            status=random.choice(['DRAFT', 'UNDER_REVIEW', 'SUBMITTED']),
            payment_status=payment_status,
            claim_amount=Decimal(claim_amount).quantize(Decimal('0.01')),
            paid_amount=Decimal(paid_amount).quantize(Decimal('0.01')),
            currency=voyage.currency,
            claim_deadline=claim_deadline,
            description=descriptions.get(cost_type, 'Post-deal claim'),
            assigned_to=assigned_analyst,
            created_by=created_by,
        )
        return claim

    def create_despatch_claim(self, voyage, assigned_analyst, created_by):
        """Create a despatch claim (when loading/unloading is faster than allowed)"""
        laytime_used = float(voyage.laytime_allowed) - random.uniform(10, 48)
        despatch_days = (float(voyage.laytime_allowed) - laytime_used) / 24
        claim_amount = despatch_days * 10000.00

        payment_status = random.choice(['NOT_SENT', 'SENT', 'PAID'])
        claim_deadline = timezone.now().date() + timedelta(days=random.randint(30, 180))

        if payment_status == 'PAID':
            paid_amount = claim_amount
        else:
            paid_amount = 0

        claim = Claim.objects.create(
            voyage=voyage,
            ship_owner=voyage.ship_owner,
            claim_type='DESPATCH',
            status=random.choice(['DRAFT', 'SUBMITTED']),
            payment_status=payment_status,
            laytime_used=Decimal(laytime_used).quantize(Decimal('0.01')),
            claim_amount=Decimal(claim_amount).quantize(Decimal('0.01')),
            paid_amount=Decimal(paid_amount).quantize(Decimal('0.01')),
            currency=voyage.currency,
            claim_deadline=claim_deadline,
            description=f'Despatch claim for voyage {voyage.voyage_number}. Completed {despatch_days:.2f} days early.',
            assigned_to=assigned_analyst,
            created_by=created_by,
        )
        return claim
