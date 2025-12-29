from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from ships.models import TCFleet
from claims.models import User


class Command(BaseCommand):
    help = 'Adds 500 redelivered TC Fleet contracts'

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
    ]

    OWNERS = [
        'Euronav Ship Management', 'Frontline Management', 'Teekay Shipping',
        'DHT Holdings', 'International Seaways', 'Nordic American Tankers',
        'Scorpio Tankers', 'Tsakos Energy Navigation', 'Okeanis Eco Tankers',
    ]

    TECHNICAL_MANAGERS = ['V.Ships', 'Anglo-Eastern', 'Thome Ship Management']
    BROKERS = ['Simpson Spence Young', 'Clarkson PLC', 'Braemar ACM']
    TRADERS = ['John Anderson', 'Sarah Mitchell', 'Michael Chen', 'Emma Thompson']
    FLAGS = ['Marshall Islands', 'Liberia', 'Panama', 'Singapore']
    LOCATIONS = ['Singapore', 'Rotterdam', 'Houston', 'Fujairah', 'Gibraltar']

    def handle(self, *args, **kwargs):
        self.stdout.write('Adding 500 redelivered TC Fleet contracts...')

        # Get admin user
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin_user = None

        # Get existing IMOs
        existing_imos = list(TCFleet.objects.values_list('imo_number', flat=True).distinct())
        existing_radar_deals = set(TCFleet.objects.values_list('radar_deal_number', flat=True))

        # Select 60 existing IMOs for historical contracts
        historical_imos = random.sample(existing_imos, min(60, len(existing_imos)))

        redelivered_count = 0
        used_imos = set(existing_imos)

        for i in range(500):
            # 40% chance to use existing IMO
            if i < 200 and historical_imos:
                imo = random.choice(historical_imos)
                ship_name = random.choice(self.SHIP_NAMES)
            else:
                imo = self._generate_unique_imo(used_imos)
                used_imos.add(imo)
                ship_name = random.choice(self.SHIP_NAMES)

            radar_deal = self._generate_unique_radar_deal(existing_radar_deals)
            existing_radar_deals.add(radar_deal)

            # Create redelivered contract
            self._create_redelivered_contract(imo, radar_deal, ship_name, admin_user)
            redelivered_count += 1

            if redelivered_count % 100 == 0:
                self.stdout.write(f'  Created {redelivered_count}/500 contracts...')

        self.stdout.write(self.style.SUCCESS(f'Successfully added {redelivered_count} redelivered contracts'))

    def _generate_unique_imo(self, used_imos):
        while True:
            imo = f"IMO{random.randint(9000000, 9999999)}"
            if imo not in used_imos:
                return imo

    def _generate_unique_radar_deal(self, existing_deals):
        while True:
            radar_deal = f"A{random.randint(1000000, 9999999)}"
            if radar_deal not in existing_deals:
                return radar_deal

    def _create_redelivered_contract(self, imo, radar_deal, ship_name, created_by):
        today = timezone.now().date()

        # Past contracts
        days_since_delivery = random.randint(730, 3650)
        charter_length_days = random.randint(365, 1095)

        delivery_date = today - timedelta(days=days_since_delivery)
        redelivery_date = delivery_date + timedelta(days=charter_length_days)
        charter_length_years = Decimal(str(round(charter_length_days / 365, 2)))
        tcp_date = delivery_date - timedelta(days=random.randint(30, 90))

        ship_type = random.choice(['AFRAMAX', 'SUEZMAX', 'VLCC', 'PANAMAX', 'MR'])
        rate_ranges = {
            'VLCC': (50000, 80000),
            'SUEZMAX': (35000, 60000),
            'AFRAMAX': (25000, 45000),
            'PANAMAX': (20000, 35000),
            'MR': (18000, 30000),
        }
        min_rate, max_rate = rate_ranges.get(ship_type, (20000, 40000))
        tc_rate_monthly = Decimal(str(random.randint(min_rate, max_rate)))

        dwt_ranges = {
            'VLCC': (280000, 320000),
            'SUEZMAX': (140000, 165000),
            'AFRAMAX': (95000, 120000),
            'PANAMAX': (60000, 85000),
            'MR': (45000, 55000),
        }
        min_dwt, max_dwt = dwt_ranges.get(ship_type, (50000, 100000))
        summer_dwt = Decimal(str(random.randint(min_dwt, max_dwt)))

        TCFleet.objects.create(
            ship_name=ship_name,
            imo_number=imo,
            ship_type=ship_type,
            delivery_status='REDELIVERED',
            trade=random.choice(['CRUDE', 'PRODUCTS', 'CHEMICAL']),
            owner_name=random.choice(self.OWNERS),
            owner_email=f"chartering@owner{random.randint(1,9)}.com",
            technical_manager=random.choice(self.TECHNICAL_MANAGERS),
            technical_manager_email=f"ops@techman{random.randint(1,9)}.com",
            charter_length_years=charter_length_years,
            tc_rate_monthly=tc_rate_monthly,
            radar_deal_number=radar_deal,
            delivery_date=delivery_date,
            redelivery_date=redelivery_date,
            tcp_date=tcp_date,
            broker_name=random.choice(self.BROKERS),
            broker_email=f"broker@broker{random.randint(1,9)}.com",
            broker_commission=Decimal(str(random.choice([1.25, 1.5, 2.0, 2.5]))),
            delivery_location=random.choice(self.LOCATIONS),
            redelivery_location=random.choice(self.LOCATIONS),
            bunkers_policy=random.choice(['CHARTERER', 'OWNER', 'SHARED']),
            summer_dwt=summer_dwt,
            built_year=random.randint(2000, 2020),
            flag=random.choice(self.FLAGS),
            next_drydock_date=None,
            trader_name=random.choice(self.TRADERS),
            created_by=created_by,
        )
