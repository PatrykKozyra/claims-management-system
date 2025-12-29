from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

from ships.models import TCFleet, Ship
from claims.models import User


class Command(BaseCommand):
    help = 'Populates TC Fleet with 150 active ships and 500 redelivered ships'

    # Ship names pool (realistic tanker names)
    SHIP_NAMES = [
        'ADVANTAGE ATOM', 'ADVANTAGE AMBER', 'ADVANTAGE ARROW', 'ADVANTAGE ATLAS',
        'BRAVE TRADER', 'BRAVE VOYAGER', 'BRAVE WARRIOR', 'BRAVE WIND',
        'CRYSTAL ENERGY', 'CRYSTAL EXPLORER', 'CRYSTAL LEGEND', 'CRYSTAL LIGHT',
        'DIAMOND OCEAN', 'DIAMOND PIONEER', 'DIAMOND PRIDE', 'DIAMOND QUEEN',
        'EAGLE SPIRIT', 'EAGLE STAR', 'EAGLE STORM', 'EAGLE STRENGTH',
        'FORTUNE LEADER', 'FORTUNE LIBERTY', 'FORTUNE LION', 'FORTUNE LOTUS',
        'GOLDEN WAVE', 'GOLDEN WIND', 'GOLDEN WING', 'GOLDEN WISDOM',
        'HARMONY OCEAN', 'HARMONY PACIFIC', 'HARMONY PEARL', 'HARMONY PHOENIX',
        'IMPERIAL DRAGON', 'IMPERIAL EAGLE', 'IMPERIAL ELITE', 'IMPERIAL EMPIRE',
        'JADE BREEZE', 'JADE BRILLIANCE', 'JADE DYNASTY', 'JADE EMERALD',
        'KING OCEAN', 'KING PACIFIC', 'KING PEARL', 'KING POSEIDON',
        'LIBERTY OCEAN', 'LIBERTY PACIFIC', 'LIBERTY PEARL', 'LIBERTY PRIDE',
        'MAJESTIC OCEAN', 'MAJESTIC PACIFIC', 'MAJESTIC PEARL', 'MAJESTIC PRIDE',
        'NAVIGATOR OCEAN', 'NAVIGATOR PACIFIC', 'NAVIGATOR PEARL', 'NAVIGATOR PRIDE',
        'OCEAN DIAMOND', 'OCEAN DRAGON', 'OCEAN DREAM', 'OCEAN DYNASTY',
        'PACIFIC LEADER', 'PACIFIC LEGEND', 'PACIFIC LIBERTY', 'PACIFIC LION',
        'QUEEN ATLANTIC', 'QUEEN CRYSTAL', 'QUEEN DIAMOND', 'QUEEN EMERALD',
        'ROYAL OCEAN', 'ROYAL PACIFIC', 'ROYAL PEARL', 'ROYAL PRIDE',
        'SAPPHIRE OCEAN', 'SAPPHIRE PACIFIC', 'SAPPHIRE PEARL', 'SAPPHIRE PRIDE',
        'TITAN OCEAN', 'TITAN PACIFIC', 'TITAN PEARL', 'TITAN PRIDE',
        'UNITY OCEAN', 'UNITY PACIFIC', 'UNITY PEARL', 'UNITY PRIDE',
        'VICTORY OCEAN', 'VICTORY PACIFIC', 'VICTORY PEARL', 'VICTORY PRIDE',
        'WARRIOR OCEAN', 'WARRIOR PACIFIC', 'WARRIOR PEARL', 'WARRIOR PRIDE',
        'ZENITH OCEAN', 'ZENITH PACIFIC', 'ZENITH PEARL', 'ZENITH PRIDE',
    ]

    OWNERS = [
        'Euronav Ship Management', 'Frontline Management', 'Teekay Shipping',
        'DHT Holdings', 'International Seaways', 'Nordic American Tankers',
        'Scorpio Tankers', 'Tsakos Energy Navigation', 'Okeanis Eco Tankers',
        'Capital Maritime', 'Top Ships', 'Hafnia Tankers',
        'Product Shipping & Trading', 'StealthGas', 'Dorian LPG',
        'BW Group', 'Navigator Gas', 'Golar LNG',
    ]

    TECHNICAL_MANAGERS = [
        'V.Ships', 'Anglo-Eastern', 'Thome Ship Management',
        'Wilhelmsen Ship Management', 'Barber Ship Management',
        'Columbia Shipmanagement', 'OSM Maritime', 'Bernhard Schulte',
    ]

    BROKERS = [
        'Simpson Spence Young', 'Clarkson PLC', 'Braemar ACM',
        'Howe Robinson', 'RS Platou', 'ICAP Shipping',
        'Fearnleys', 'Poten & Partners', 'McQuilling Partners',
    ]

    TRADERS = [
        'John Anderson', 'Sarah Mitchell', 'Michael Chen', 'Emma Thompson',
        'David Rodriguez', 'Lisa Wang', 'James Peterson', 'Maria Garcia',
        'Robert Taylor', 'Jennifer Lee', 'William Brown', 'Jessica Wilson',
    ]

    FLAGS = [
        'Marshall Islands', 'Liberia', 'Panama', 'Singapore',
        'Hong Kong', 'Malta', 'Bahamas', 'Greece', 'Cyprus'
    ]

    LOCATIONS = [
        'Singapore', 'Rotterdam', 'Houston', 'Fujairah', 'Gibraltar',
        'Antwerp', 'Hamburg', 'Tokyo', 'Shanghai', 'Dubai',
        'Mumbai', 'Suez', 'Malta', 'Piraeus', 'New York'
    ]

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating TC Fleet dummy data...')

        # Get or create admin user
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin_user = None

        # Track used IMO numbers and RADAR deal numbers
        used_imos = set()
        used_radar_deals = set()
        created_count = 0

        # Generate 150 active contracts (ON_TC and INCOMING_TC)
        self.stdout.write('Creating 150 active TC contracts...')
        for i in range(150):
            # Generate unique IMO number
            imo = self._generate_unique_imo(used_imos)
            used_imos.add(imo)

            # Generate unique RADAR deal number
            radar_deal = self._generate_unique_radar_deal(used_radar_deals)
            used_radar_deals.add(radar_deal)

            # Determine status (120 ON_TC, 30 INCOMING_TC)
            if i < 120:
                delivery_status = 'ON_TC'
                # Contracts delivered in the past, redelivery in the future
                days_since_delivery = random.randint(30, 730)  # 1 month to 2 years ago
                days_until_redelivery = random.randint(30, 730)  # 1 month to 2 years ahead
            else:
                delivery_status = 'INCOMING_TC'
                # Future delivery
                days_since_delivery = -random.randint(10, 90)  # 10-90 days in future
                days_until_redelivery = days_since_delivery + random.randint(365, 1095)  # 1-3 years charter

            contract = self._create_contract(
                imo=imo,
                radar_deal=radar_deal,
                delivery_status=delivery_status,
                days_since_delivery=days_since_delivery,
                days_until_redelivery=days_until_redelivery,
                created_by=admin_user,
            )
            created_count += 1

            if (i + 1) % 50 == 0:
                self.stdout.write(f'  Created {i + 1}/150 active contracts...')

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} active TC contracts'))

        # Generate 500 redelivered contracts
        self.stdout.write('Creating 500 redelivered TC contracts...')
        redelivered_count = 0

        # Some will be for the same ships as active contracts (historical contracts)
        # 40% will be historical contracts for existing ships
        historical_imos = random.sample(list(used_imos), min(60, len(used_imos)))

        for i in range(500):
            # 40% chance to use an existing IMO (historical contract)
            if i < 200 and historical_imos:
                imo = random.choice(historical_imos)
                # Ship name might have changed
                ship_name = random.choice(self.SHIP_NAMES)
            else:
                # New IMO
                imo = self._generate_unique_imo(used_imos)
                used_imos.add(imo)
                ship_name = random.choice(self.SHIP_NAMES)

            # Generate unique RADAR deal number
            radar_deal = self._generate_unique_radar_deal(used_radar_deals)
            used_radar_deals.add(radar_deal)

            # Redelivered contracts - in the past
            days_since_delivery = random.randint(730, 3650)  # 2-10 years ago
            charter_length_days = random.randint(365, 1095)  # 1-3 years
            days_until_redelivery = days_since_delivery - charter_length_days

            contract = self._create_contract(
                imo=imo,
                radar_deal=radar_deal,
                delivery_status='REDELIVERED',
                days_since_delivery=days_since_delivery,
                days_until_redelivery=days_until_redelivery,
                created_by=admin_user,
                ship_name=ship_name,
            )
            redelivered_count += 1

            if (redelivered_count) % 100 == 0:
                self.stdout.write(f'  Created {redelivered_count}/500 redelivered contracts...')

        self.stdout.write(self.style.SUCCESS(f'Created {redelivered_count} redelivered TC contracts'))
        self.stdout.write(self.style.SUCCESS(f'\nTotal TC Fleet contracts created: {created_count + redelivered_count}'))
        self.stdout.write(f'  Unique ships (IMOs): {len(used_imos)}')

    def _generate_unique_imo(self, used_imos):
        """Generate a unique IMO number"""
        while True:
            imo = f"IMO{random.randint(9000000, 9999999)}"
            if imo not in used_imos:
                return imo

    def _generate_unique_radar_deal(self, used_radar_deals):
        """Generate a unique RADAR deal number (format: A1234567)"""
        while True:
            radar_deal = f"A{random.randint(1000000, 9999999)}"
            if radar_deal not in used_radar_deals:
                return radar_deal

    def _create_contract(self, imo, radar_deal, delivery_status, days_since_delivery,
                        days_until_redelivery, created_by, ship_name=None):
        """Create a single TC Fleet contract"""
        today = timezone.now().date()

        # Ship details
        if ship_name is None:
            ship_name = random.choice(self.SHIP_NAMES)
        ship_type = random.choice(['AFRAMAX', 'SUEZMAX', 'VLCC', 'PANAMAX', 'MR', 'LR1', 'LR2'])
        trade = random.choice(['CRUDE', 'PRODUCTS', 'CHEMICAL'])

        # Dates
        delivery_date = today - timedelta(days=days_since_delivery)
        redelivery_date = today + timedelta(days=days_until_redelivery)
        charter_length_years = Decimal(str(round((redelivery_date - delivery_date).days / 365, 2)))
        tcp_date = delivery_date - timedelta(days=random.randint(30, 90))

        # Owner and technical manager
        owner_name = random.choice(self.OWNERS)
        owner_email = f"chartering@{owner_name.lower().replace(' ', '')}.com"
        technical_manager = random.choice(self.TECHNICAL_MANAGERS)
        technical_manager_email = f"operations@{technical_manager.lower().replace(' ', '')}.com"

        # Charter rates (realistic monthly rates based on ship type)
        rate_ranges = {
            'VLCC': (50000, 80000),
            'SUEZMAX': (35000, 60000),
            'AFRAMAX': (25000, 45000),
            'PANAMAX': (20000, 35000),
            'MR': (18000, 30000),
            'LR1': (22000, 38000),
            'LR2': (25000, 42000),
        }
        min_rate, max_rate = rate_ranges.get(ship_type, (20000, 40000))
        tc_rate_monthly = Decimal(str(random.randint(min_rate, max_rate)))

        # Broker
        broker_name = random.choice(self.BROKERS)
        broker_email = f"broker@{broker_name.lower().replace(' ', '')}.com"
        broker_commission = Decimal(str(random.choice([1.25, 1.5, 2.0, 2.5])))

        # Locations
        delivery_location = random.choice(self.LOCATIONS)
        redelivery_location = random.choice(self.LOCATIONS)

        # Technical specs
        dwt_ranges = {
            'VLCC': (280000, 320000),
            'SUEZMAX': (140000, 165000),
            'AFRAMAX': (95000, 120000),
            'PANAMAX': (60000, 85000),
            'MR': (45000, 55000),
            'LR1': (55000, 75000),
            'LR2': (75000, 95000),
        }
        min_dwt, max_dwt = dwt_ranges.get(ship_type, (50000, 100000))
        summer_dwt = Decimal(str(random.randint(min_dwt, max_dwt)))

        built_year = random.randint(2005, 2023)
        flag = random.choice(self.FLAGS)
        bunkers_policy = random.choice(['CHARTERER', 'OWNER', 'SHARED'])

        # Internal
        trader_name = random.choice(self.TRADERS)

        # Dry-dock date (if relevant)
        if delivery_status in ['ON_TC', 'INCOMING_TC']:
            next_drydock_date = today + timedelta(days=random.randint(180, 730))
        else:
            next_drydock_date = None

        # Create contract
        contract = TCFleet.objects.create(
            ship_name=ship_name,
            imo_number=imo,
            ship_type=ship_type,
            delivery_status=delivery_status,
            trade=trade,
            owner_name=owner_name,
            owner_email=owner_email,
            technical_manager=technical_manager,
            technical_manager_email=technical_manager_email,
            charter_length_years=charter_length_years,
            tc_rate_monthly=tc_rate_monthly,
            radar_deal_number=radar_deal,
            delivery_date=delivery_date,
            redelivery_date=redelivery_date,
            tcp_date=tcp_date,
            broker_name=broker_name,
            broker_email=broker_email,
            broker_commission=broker_commission,
            delivery_location=delivery_location,
            redelivery_location=redelivery_location,
            bunkers_policy=bunkers_policy,
            summer_dwt=summer_dwt,
            built_year=built_year,
            flag=flag,
            next_drydock_date=next_drydock_date,
            trader_name=trader_name,
            created_by=created_by,
        )

        return contract
