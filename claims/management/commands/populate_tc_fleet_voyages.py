from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from claims.models import User, ShipOwner, Voyage, Claim, VoyageAssignment
from ships.models import TCFleet


class Command(BaseCommand):
    help = 'Generate dummy voyages and claims for TC Fleet ships (TRADED type)'

    LOAD_PORTS = [
        'Ras Tanura', 'Basra', 'Kuwait', 'Abu Dhabi', 'Kharg Island',
        'Rotterdam', 'Houston', 'Singapore', 'Fujairah', 'Yanbu',
        'Jeddah', 'Shuaiba', 'Mina Al Ahmadi', 'Das Island', 'Zirku',
    ]

    DISCHARGE_PORTS = [
        'Rotterdam', 'Singapore', 'Ningbo', 'Shanghai', 'Busan',
        'Yokohama', 'Ulsan', 'Yeosu', 'Chiba', 'Kawasaki',
        'Mumbai', 'Chennai', 'Visakhapatnam', 'Paradip', 'Jamnagar',
        'Antwerp', 'Hamburg', 'Le Havre', 'Marseille', 'Trieste',
    ]

    CHARTER_PARTIES = [
        'ASBATANKVOY', 'BPVOY4', 'SHELLVOY6', 'EXXONVOY2012',
        'INTERTANKVOY76', 'SHELL TIME 4', 'BP TIME 3',
    ]

    CLAIM_TYPES = [
        'Demurrage', 'Despatch', 'Detention', 'Off-hire',
        'Bunker Claim', 'Damage Claim', 'Contamination',
    ]

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating dummy voyages and claims for TC Fleet ships...')

        # Get admin user
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user not found. Please create admin user first.'))
            return

        # Get all users with WRITE role for assignment
        analysts = list(User.objects.filter(role__in=['WRITE', 'TEAM_LEAD', 'ADMIN']))
        if not analysts:
            analysts = [admin_user]

        # Get active TC Fleet vessels (ON_TC status)
        tc_vessels = TCFleet.objects.filter(delivery_status='ON_TC')

        if not tc_vessels.exists():
            self.stdout.write(self.style.WARNING('No active TC Fleet vessels found.'))
            return

        voyages_created = 0
        claims_created = 0

        for tc_vessel in tc_vessels:
            # Create 2-4 voyages per vessel
            num_voyages = random.randint(2, 4)

            for i in range(num_voyages):
                # Get or create ship owner
                owner, _ = ShipOwner.objects.get_or_create(
                    name=tc_vessel.owner_name,
                    defaults={
                        'code': f'OWN{random.randint(1000, 9999)}',
                        'is_active': True,
                    }
                )

                # Generate voyage dates
                days_ago = random.randint(30, 180)
                laycan_start = timezone.now().date() - timedelta(days=days_ago)
                laycan_end = laycan_start + timedelta(days=random.randint(2, 5))

                # Generate unique voyage number
                voyage_number = f"{tc_vessel.ship_name[:3].upper()}{random.randint(1000, 9999)}"
                radar_id = f"RADAR-TC-{tc_vessel.imo_number}-{random.randint(10000, 99999)}"

                # Create voyage
                voyage = Voyage.objects.create(
                    radar_voyage_id=radar_id,
                    voyage_number=voyage_number,
                    vessel_name=tc_vessel.ship_name,
                    imo_number=tc_vessel.imo_number,
                    charter_type='TRADED',  # TC Fleet ships are TRADED
                    charter_party=random.choice(self.CHARTER_PARTIES),
                    load_port=random.choice(self.LOAD_PORTS),
                    discharge_port=random.choice(self.DISCHARGE_PORTS),
                    laycan_start=laycan_start,
                    laycan_end=laycan_end,
                    ship_owner=owner,
                    demurrage_rate=Decimal(str(random.uniform(15000, 45000))),
                    laytime_allowed=Decimal(str(random.uniform(24, 72))),
                    currency='USD',
                    assignment_status='ASSIGNED' if random.random() > 0.3 else 'UNASSIGNED',
                )

                # Assign to analyst if assigned status
                if voyage.assignment_status == 'ASSIGNED':
                    analyst = random.choice(analysts)
                    voyage.assigned_analyst = analyst
                    voyage.assigned_at = timezone.now()
                    voyage.save()

                    # Create assignment history
                    VoyageAssignment.objects.create(
                        voyage=voyage,
                        assigned_to=analyst,
                        assigned_by=admin_user,
                        is_active=True,
                    )

                voyages_created += 1

                # Create 0-2 claims for each voyage
                num_claims = random.randint(0, 2)
                for j in range(num_claims):
                    claim_type = random.choice(self.CLAIM_TYPES)

                    # Generate claim amount based on type
                    if claim_type == 'Demurrage':
                        amount = Decimal(str(random.uniform(50000, 300000)))
                    elif claim_type == 'Despatch':
                        amount = Decimal(str(random.uniform(10000, 80000)))
                    elif claim_type == 'Off-hire':
                        amount = Decimal(str(random.uniform(100000, 500000)))
                    else:
                        amount = Decimal(str(random.uniform(20000, 150000)))

                    # Payment status
                    payment_status = random.choice(['UNPAID', 'PARTIALLY_PAID', 'PAID'])

                    claim = Claim.objects.create(
                        voyage=voyage,
                        claim_number=f"CLM-{voyage_number}-{j+1:02d}",
                        claim_type=claim_type,
                        ship_owner=owner,
                        claim_amount=amount,
                        currency='USD',
                        payment_status=payment_status,
                        description=f"{claim_type} claim for voyage {voyage_number}",
                        assigned_to=voyage.assigned_analyst if voyage.assigned_analyst else None,
                        created_by=admin_user,
                    )

                    claims_created += 1

                if voyages_created % 10 == 0:
                    self.stdout.write(f'  Created {voyages_created} voyages and {claims_created} claims...')

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {voyages_created} TRADED voyages and {claims_created} claims'
        ))
