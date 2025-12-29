from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from ships.models import ShipSpecification, TCFleet
from claims.models import User


class Command(BaseCommand):
    help = 'Populate Ship Specifications (Q88) for TC Fleet vessels'

    CALL_SIGNS = ['9HAA4', '9VYR2', 'VRKE8', 'C6QA9', '3EXY5', 'A8MN2', 'V7XP6', 'H3BS9']

    CLASSIFICATION_SOCIETIES = [
        'Lloyd\'s Register (LR)',
        'American Bureau of Shipping (ABS)',
        'Det Norske Veritas (DNV)',
        'Bureau Veritas (BV)',
        'Nippon Kaiji Kyokai (NK)',
    ]

    CLASS_NOTATIONS = [
        '✠ 100A1, Oil Tanker, ESP, BC-A, CLEAN, SYS-NEQ-2, HMON',
        '✠ A1, Tanker for Oil & Petroleum Products, ESP, AMS, ACCU',
        '✠ 100A5, Oil Tanker, ESP, ICE-1A, BC-A, CLEAN DESIGN',
        '✠ 1A1, Oil Tanker, ESP, E0, NAUTICUS (Newbuilding)',
    ]

    SHIPYARDS = [
        'Hyundai Heavy Industries, South Korea',
        'Daewoo Shipbuilding & Marine Engineering, South Korea',
        'Samsung Heavy Industries, South Korea',
        'Mitsubishi Heavy Industries, Japan',
        'Imabari Shipbuilding, Japan',
        'China State Shipbuilding Corporation, China',
    ]

    ENGINE_TYPES = [
        'MAN B&W 6S60MC-C',
        'MAN B&W 7S70MC-C',
        'Wärtsilä 6RT-flex58T',
        'MAN B&W 5S70ME-C',
        'Wärtsilä-Sulzer 7RTA84C',
        'MAN B&W 6S80MC-C',
    ]

    ENGINE_BUILDERS = [
        'Hyundai Heavy Industries Engine & Machinery Division',
        'MAN Diesel & Turbo',
        'Wärtsilä Finland',
        'Doosan Engine',
    ]

    P_AND_I_CLUBS = [
        'Gard P&I Club',
        'UK P&I Club',
        'Skuld P&I',
        'West of England P&I',
        'American Club',
        'Britannia P&I',
    ]

    ICE_CLASSES = ['', '', '', 'ICE-1A', 'ICE-1B', 'ICE-1C']

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating Ship Specifications (Q88) for TC Fleet vessels...')

        # Get admin user
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin_user = None

        # Get all unique IMOs from TC Fleet
        tc_fleet_imos = TCFleet.objects.values_list('imo_number', flat=True).distinct()

        # Get TC Fleet contracts to extract vessel info
        tc_contracts = {}
        for imo in tc_fleet_imos:
            contract = TCFleet.objects.filter(imo_number=imo).first()
            tc_contracts[imo] = contract

        created_count = 0

        for imo in tc_fleet_imos:
            # Skip if specification already exists
            if ShipSpecification.objects.filter(imo_number=imo).exists():
                self.stdout.write(f'  Specification for {imo} already exists, skipping...')
                continue

            contract = tc_contracts[imo]

            # Determine vessel type based on ship type
            if contract.ship_type in ['VLCC', 'SUEZMAX', 'AFRAMAX']:
                vessel_type = 'CRUDE'
            elif contract.ship_type in ['MR', 'LR1', 'LR2', 'PANAMAX']:
                vessel_type = 'PRODUCT'
            else:
                vessel_type = random.choice(['CRUDE', 'PRODUCT', 'CHEMICAL'])

            # Get realistic dimensions and tonnages based on ship type
            dims = self._get_ship_dimensions(contract.ship_type, float(contract.summer_dwt))

            # Generate specification
            ShipSpecification.objects.create(
                # VESSEL IDENTIFICATION
                vessel_name=contract.ship_name,
                imo_number=imo,
                call_sign=f"{random.choice(self.CALL_SIGNS)}{random.randint(100,999)}",
                flag=contract.flag,
                port_of_registry=random.choice([
                    'Majuro', 'Monrovia', 'Panama City', 'Singapore', 'Hong Kong'
                ]),
                official_number=f"{random.randint(100000,999999)}",
                vessel_type=vessel_type,
                built_year=contract.built_year,
                built_country=random.choice(['South Korea', 'Japan', 'China']),
                shipyard=random.choice(self.SHIPYARDS),
                classification_society=random.choice(self.CLASSIFICATION_SOCIETIES),
                class_notation=random.choice(self.CLASS_NOTATIONS),

                # DIMENSIONS & TONNAGES
                length_overall=Decimal(str(dims['loa'])),
                length_between_perpendiculars=Decimal(str(dims['lbp'])),
                breadth_moulded=Decimal(str(dims['breadth'])),
                depth_moulded=Decimal(str(dims['depth'])),
                summer_draft=Decimal(str(dims['draft'])),
                summer_deadweight=contract.summer_dwt,
                lightweight=Decimal(str(dims['lightweight'])),
                gross_tonnage=Decimal(str(dims['gross_tonnage'])),
                net_tonnage=Decimal(str(dims['net_tonnage'])),
                suez_canal_tonnage=Decimal(str(dims['suez_tonnage'])) if random.random() > 0.3 else None,
                panama_canal_tonnage=Decimal(str(dims['panama_tonnage'])) if random.random() > 0.3 else None,

                # CARGO CAPACITY
                total_cargo_capacity=Decimal(str(dims['cargo_capacity'])),
                number_of_cargo_tanks=dims['cargo_tanks'],
                segregated_ballast_tanks_capacity=Decimal(str(dims['ballast_capacity'])),
                slop_tank_capacity=Decimal(str(random.uniform(500, 2000))),
                cargo_tank_coating=random.choice(['EPOXY', 'ZINC', 'STAINLESS_STEEL', 'UNCOATED']),
                cargo_heating_capability=random.choice([True, False]),
                maximum_heating_temperature=Decimal(str(random.randint(60, 85))) if random.random() > 0.5 else None,

                # MACHINERY & PERFORMANCE
                main_engine_type=random.choice(self.ENGINE_TYPES),
                main_engine_power=Decimal(str(dims['engine_power'])),
                main_engine_builder=random.choice(self.ENGINE_BUILDERS),
                service_speed_laden=Decimal(str(round(random.uniform(13.5, 15.5), 1))),
                service_speed_ballast=Decimal(str(round(random.uniform(14.0, 16.0), 1))),
                fuel_consumption_laden=Decimal(str(round(dims['fuel_consumption_laden'], 1))),
                fuel_consumption_ballast=Decimal(str(round(dims['fuel_consumption_ballast'], 1))),
                fuel_type=random.choice(['VLSFO', 'MGO', 'IFO']),
                bow_thruster=random.choice([True, False]),
                stern_thruster=random.choice([True, False]),

                # CARGO HANDLING
                number_of_cargo_pumps=random.choice([3, 4, 6]),
                cargo_pump_capacity=Decimal(str(round(random.uniform(2000, 4500), 0))),
                inert_gas_system=True if vessel_type == 'CRUDE' else random.choice([True, False]),
                crude_oil_washing=True if vessel_type == 'CRUDE' else False,
                vapor_recovery_system=random.choice([True, False]),
                cargo_manifold_size=Decimal(str(random.choice([12, 14, 16, 18]))),
                cargo_manifold_pressure_rating=Decimal(str(random.choice([10, 16, 25]))),

                # ENVIRONMENTAL & SAFETY
                double_hull=True,
                ice_class=random.choice(self.ICE_CLASSES),
                oil_pollution_prevention_certificate_expiry=timezone.now().date() + timedelta(days=random.randint(180, 1095)),
                safety_management_certificate_expiry=timezone.now().date() + timedelta(days=random.randint(180, 1095)),
                safety_equipment_certificate_expiry=timezone.now().date() + timedelta(days=random.randint(180, 730)),
                international_oil_pollution_certificate_expiry=timezone.now().date() + timedelta(days=random.randint(180, 1095)),
                ship_sanitation_certificate_expiry=timezone.now().date() + timedelta(days=random.randint(180, 730)),

                # OPERATIONAL REQUIREMENTS
                minimum_freeboard_laden=Decimal(str(round(random.uniform(3.0, 8.0), 2))),
                air_draft_ballast=Decimal(str(round(random.uniform(50, 70), 2))),
                air_draft_laden=Decimal(str(round(random.uniform(45, 65), 2))),
                maximum_allowed_draft_restriction=Decimal(str(dims['draft'])),
                port_restrictions='' if random.random() > 0.3 else 'US Port restrictions apply. SIRE inspection required.',
                special_requirements='' if random.random() > 0.5 else 'COW certified. USCG compliant.',

                # COMMERCIAL
                owner_name=contract.owner_name,
                operator_name=contract.owner_name,
                commercial_manager=contract.owner_name,
                technical_manager=contract.technical_manager,
                p_and_i_club=random.choice(self.P_AND_I_CLUBS),

                # METADATA
                created_by=admin_user,
            )

            created_count += 1
            if created_count % 50 == 0:
                self.stdout.write(f'  Created {created_count} specifications...')

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} ship specifications'))

    def _get_ship_dimensions(self, ship_type, dwt):
        """Generate realistic dimensions based on ship type and DWT"""

        if ship_type == 'VLCC':
            return {
                'loa': round(random.uniform(320, 340), 2),
                'lbp': round(random.uniform(310, 330), 2),
                'breadth': round(random.uniform(58, 63), 2),
                'depth': round(random.uniform(28, 32), 2),
                'draft': round(random.uniform(21, 23), 2),
                'lightweight': round(dwt * 0.12, 2),
                'gross_tonnage': round(dwt * 0.50, 2),
                'net_tonnage': round(dwt * 0.35, 2),
                'suez_tonnage': round(dwt * 0.52, 2),
                'panama_tonnage': round(dwt * 0.48, 2),
                'cargo_capacity': round(dwt * 1.15, 0),
                'cargo_tanks': random.choice([12, 14, 16]),
                'ballast_capacity': round(dwt * 0.35, 2),
                'engine_power': round(random.uniform(25000, 30000), 2),
                'fuel_consumption_laden': round(random.uniform(70, 95), 1),
                'fuel_consumption_ballast': round(random.uniform(65, 85), 1),
            }
        elif ship_type == 'SUEZMAX':
            return {
                'loa': round(random.uniform(270, 285), 2),
                'lbp': round(random.uniform(260, 275), 2),
                'breadth': round(random.uniform(46, 50), 2),
                'depth': round(random.uniform(23, 26), 2),
                'draft': round(random.uniform(16, 18), 2),
                'lightweight': round(dwt * 0.13, 2),
                'gross_tonnage': round(dwt * 0.52, 2),
                'net_tonnage': round(dwt * 0.37, 2),
                'suez_tonnage': round(dwt * 0.53, 2),
                'panama_tonnage': round(dwt * 0.49, 2),
                'cargo_capacity': round(dwt * 1.18, 0),
                'cargo_tanks': random.choice([10, 12, 14]),
                'ballast_capacity': round(dwt * 0.37, 2),
                'engine_power': round(random.uniform(18000, 23000), 2),
                'fuel_consumption_laden': round(random.uniform(55, 70), 1),
                'fuel_consumption_ballast': round(random.uniform(50, 65), 1),
            }
        elif ship_type == 'AFRAMAX':
            return {
                'loa': round(random.uniform(240, 250), 2),
                'lbp': round(random.uniform(230, 245), 2),
                'breadth': round(random.uniform(42, 46), 2),
                'depth': round(random.uniform(20, 23), 2),
                'draft': round(random.uniform(14, 16), 2),
                'lightweight': round(dwt * 0.14, 2),
                'gross_tonnage': round(dwt * 0.54, 2),
                'net_tonnage': round(dwt * 0.38, 2),
                'suez_tonnage': round(dwt * 0.55, 2),
                'panama_tonnage': round(dwt * 0.50, 2),
                'cargo_capacity': round(dwt * 1.20, 0),
                'cargo_tanks': random.choice([10, 12]),
                'ballast_capacity': round(dwt * 0.38, 2),
                'engine_power': round(random.uniform(14000, 18000), 2),
                'fuel_consumption_laden': round(random.uniform(45, 58), 1),
                'fuel_consumption_ballast': round(random.uniform(40, 52), 1),
            }
        elif ship_type in ['PANAMAX', 'MR', 'LR1', 'LR2']:
            return {
                'loa': round(random.uniform(180, 230), 2),
                'lbp': round(random.uniform(175, 225), 2),
                'breadth': round(random.uniform(30, 42), 2),
                'depth': round(random.uniform(16, 20), 2),
                'draft': round(random.uniform(11, 14), 2),
                'lightweight': round(dwt * 0.16, 2),
                'gross_tonnage': round(dwt * 0.58, 2),
                'net_tonnage': round(dwt * 0.40, 2),
                'suez_tonnage': round(dwt * 0.57, 2),
                'panama_tonnage': round(dwt * 0.52, 2),
                'cargo_capacity': round(dwt * 1.25, 0),
                'cargo_tanks': random.choice([8, 10, 12]),
                'ballast_capacity': round(dwt * 0.40, 2),
                'engine_power': round(random.uniform(10000, 14000), 2),
                'fuel_consumption_laden': round(random.uniform(35, 45), 1),
                'fuel_consumption_ballast': round(random.uniform(30, 40), 1),
            }
        else:
            # Default for other types
            return {
                'loa': round(random.uniform(150, 200), 2),
                'lbp': round(random.uniform(145, 195), 2),
                'breadth': round(random.uniform(25, 35), 2),
                'depth': round(random.uniform(14, 18), 2),
                'draft': round(random.uniform(9, 12), 2),
                'lightweight': round(dwt * 0.18, 2),
                'gross_tonnage': round(dwt * 0.60, 2),
                'net_tonnage': round(dwt * 0.42, 2),
                'suez_tonnage': round(dwt * 0.58, 2),
                'panama_tonnage': round(dwt * 0.53, 2),
                'cargo_capacity': round(dwt * 1.28, 0),
                'cargo_tanks': random.choice([6, 8, 10]),
                'ballast_capacity': round(dwt * 0.42, 2),
                'engine_power': round(random.uniform(7000, 10000), 2),
                'fuel_consumption_laden': round(random.uniform(25, 35), 1),
                'fuel_consumption_ballast': round(random.uniform(22, 32), 1),
            }
