from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from port_activities.models import PortActivity, ActivityType
from claims.models import User, Voyage
from ships.models import Ship


class Command(BaseCommand):
    help = 'Generate dummy port activities for voyages'

    # Activity sequences for different voyage types
    TYPICAL_VOYAGE_SEQUENCE = [
        'in_transit',
        'waiting_for_berth',
        'pilot_onboard',
        'berthing',
        'load',
        'bunkering',
        'unberthing',
        'in_transit',
        'canal_transit',
        'in_transit',
        'pilot_onboard',
        'berthing',
        'discharge',
        'unberthing',
        'in_transit',
    ]

    PORTS = {
        'Ras Tanura': 'Saudi Arabia',
        'Basra': 'Iraq',
        'Kuwait': 'Kuwait',
        'Abu Dhabi': 'UAE',
        'Rotterdam': 'Netherlands',
        'Houston': 'USA',
        'Singapore': 'Singapore',
        'Fujairah': 'UAE',
        'Ningbo': 'China',
        'Shanghai': 'China',
        'Mumbai': 'India',
        'Antwerp': 'Belgium',
    }

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating dummy port activities for voyages...')

        # Get admin user
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user not found.'))
            return

        # Get all voyages
        voyages = Voyage.objects.all()

        if not voyages.exists():
            self.stdout.write(self.style.WARNING('No voyages found.'))
            return

        activities_created = 0

        for voyage in voyages:
            # Get ship
            try:
                ship = Ship.objects.get(imo_number=voyage.imo_number)
            except Ship.DoesNotExist:
                # Create ship if doesn't exist
                ship = Ship.objects.create(
                    imo_number=voyage.imo_number or f"IMO{random.randint(1000000, 9999999)}",
                    vessel_name=voyage.vessel_name,
                    vessel_type=random.choice(['VLCC', 'SUEZMAX', 'AFRAMAX', 'MR', 'LR1', 'LR2']),
                    built_year=random.randint(2005, 2020),
                    flag=random.choice(['Liberia', 'Marshall Islands', 'Panama', 'Singapore', 'Malta']),
                    deadweight=Decimal(str(random.uniform(50000, 320000))),
                    charter_type='TIME_CHARTER' if voyage.charter_type == 'TRADED' else 'SPOT',
                    is_tc_fleet=voyage.charter_type == 'TRADED',
                )

            # Generate 3-8 activities for this voyage
            num_activities = random.randint(3, 8)

            # Start date is around laycan start
            current_datetime = timezone.make_aware(
                timezone.datetime.combine(voyage.laycan_start, timezone.datetime.min.time())
            ) - timedelta(days=random.randint(5, 15))

            for i in range(num_activities):
                # Select activity type
                if i == 0:
                    activity_code = 'in_transit'
                elif i < num_activities - 1:
                    activity_code = random.choice([
                        'load', 'discharge', 'bunkering', 'berthing', 'unberthing',
                        'waiting_for_berth', 'at_anchorage', 'tank_cleaning',
                        'ballasting', 'deballasting', 'in_transit', 'pilot_onboard',
                    ])
                else:
                    activity_code = 'in_transit'

                # Get activity type
                try:
                    activity_type = ActivityType.objects.get(code=activity_code)
                except ActivityType.DoesNotExist:
                    continue

                # Determine port
                if i < num_activities // 2:
                    port_name = voyage.load_port
                else:
                    port_name = voyage.discharge_port

                # Activity duration
                if activity_code in ['load', 'discharge']:
                    duration_hours = random.uniform(12, 48)
                elif activity_code == 'in_transit':
                    duration_hours = random.uniform(72, 240)
                elif activity_code in ['bunkering', 'tank_cleaning']:
                    duration_hours = random.uniform(4, 12)
                elif activity_code in ['berthing', 'unberthing']:
                    duration_hours = random.uniform(1, 3)
                else:
                    duration_hours = random.uniform(2, 24)

                start_datetime = current_datetime
                end_datetime = start_datetime + timedelta(hours=duration_hours)

                # Date status (70% actual, 30% estimated for past dates)
                if start_datetime < timezone.now():
                    date_status = 'ACTUAL' if random.random() > 0.3 else 'ESTIMATED'
                else:
                    date_status = 'ESTIMATED'

                # Cargo quantity for loading/discharging activities
                cargo_quantity = None
                if activity_code in ['load', 'discharge', 'part_load', 'part_discharge']:
                    cargo_quantity = Decimal(str(random.uniform(30000, 280000)))

                # System notes
                notes_options = [
                    f"Activity synchronized from RADAR at {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                    "Data pulled from vessel AIS system",
                    "Confirmed by vessel master via email",
                    "Updated based on port agent report",
                    "",
                ]

                # Create activity
                activity = PortActivity.objects.create(
                    ship=ship,
                    voyage=voyage,
                    activity_type=activity_type,
                    port_name=port_name,
                    load_port=voyage.load_port if activity_code in ['load', 'part_load'] else '',
                    discharge_port=voyage.discharge_port if activity_code in ['discharge', 'part_discharge'] else '',
                    start_datetime=start_datetime,
                    start_date_status=date_status,
                    end_datetime=end_datetime,
                    end_date_status=date_status,
                    cargo_quantity=cargo_quantity,
                    notes=random.choice(notes_options),
                    user_comments='',  # Empty by default
                    radar_activity_id=f"RADAR-ACT-{random.randint(100000, 999999)}",
                    last_radar_sync=timezone.now(),
                    created_by=admin_user,
                )

                activities_created += 1
                current_datetime = end_datetime + timedelta(hours=random.uniform(0.5, 6))

            if activities_created % 20 == 0:
                self.stdout.write(f'  Created {activities_created} activities...')

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {activities_created} port activities for {voyages.count()} voyages'
        ))
