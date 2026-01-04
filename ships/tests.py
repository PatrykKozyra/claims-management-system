"""
Comprehensive test suite for ships app.

Tests cover:
- Ship model functionality
- TCFleet model functionality
- ShipSpecification (Q88) model functionality
- Model properties and computed fields
- Cross-app integration
- Data validation
- Edge cases
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from ships.models import Ship, TCFleet, ShipSpecification

User = get_user_model()


@pytest.mark.django_db
class TestShipModel:
    """Test Ship model functionality"""

    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def basic_ship(self):
        """Create a basic ship for testing"""
        return Ship.objects.create(
            imo_number='IMO1234567',
            vessel_name='Test Vessel',
            vessel_type='AFRAMAX',
            built_year=2015,
            deadweight=Decimal('105000.00'),
            charter_type='SPOT'
        )

    @pytest.fixture
    def tc_ship(self):
        """Create a time charter ship"""
        today = date.today()
        return Ship.objects.create(
            imo_number='IMO9876543',
            vessel_name='TC Test Vessel',
            vessel_type='SUEZMAX',
            built_year=2018,
            deadweight=Decimal('158000.00'),
            charter_type='TIME_CHARTER',
            is_tc_fleet=True,
            charter_start_date=today - timedelta(days=30),
            charter_end_date=today + timedelta(days=60),
            daily_hire_rate=Decimal('25000.00'),
            tc_charterer='Test Charterer Inc.'
        )

    def test_ship_creation(self, basic_ship):
        """Test basic ship creation"""
        assert basic_ship.imo_number == 'IMO1234567'
        assert basic_ship.vessel_name == 'Test Vessel'
        assert basic_ship.vessel_type == 'AFRAMAX'
        assert basic_ship.built_year == 2015
        assert basic_ship.deadweight == Decimal('105000.00')
        assert basic_ship.is_active is True
        assert basic_ship.is_tc_fleet is False

    def test_ship_str_representation(self, basic_ship):
        """Test ship string representation"""
        expected = "Test Vessel (IMO: IMO1234567)"
        assert str(basic_ship) == expected

    def test_imo_number_uniqueness(self, basic_ship):
        """Test that IMO numbers must be unique"""
        with pytest.raises(IntegrityError):
            Ship.objects.create(
                imo_number='IMO1234567',  # Duplicate
                vessel_name='Another Vessel',
                vessel_type='VLCC',
                built_year=2020,
                deadweight=Decimal('300000.00')
            )

    def test_vessel_type_choices(self):
        """Test vessel type choices validation"""
        ship = Ship(
            imo_number='IMO1111111',
            vessel_name='Type Test',
            vessel_type='VLCC',
            built_year=2010,
            deadweight=Decimal('300000.00')
        )
        ship.full_clean()  # Should not raise
        ship.save()
        assert ship.vessel_type == 'VLCC'

    def test_charter_type_choices(self):
        """Test charter type choices"""
        ship = Ship.objects.create(
            imo_number='IMO2222222',
            vessel_name='Charter Test',
            vessel_type='PANAMAX',
            built_year=2012,
            deadweight=Decimal('75000.00'),
            charter_type='BAREBOAT'
        )
        assert ship.charter_type == 'BAREBOAT'

    def test_is_charter_active_true(self, tc_ship):
        """Test is_charter_active property when charter is active"""
        assert tc_ship.is_charter_active is True

    def test_is_charter_active_false_no_dates(self, basic_ship):
        """Test is_charter_active when no charter dates set"""
        assert basic_ship.is_charter_active is False

    def test_is_charter_active_false_expired(self):
        """Test is_charter_active when charter has expired"""
        today = date.today()
        ship = Ship.objects.create(
            imo_number='IMO3333333',
            vessel_name='Expired Charter',
            vessel_type='MR',
            built_year=2010,
            deadweight=Decimal('50000.00'),
            is_tc_fleet=True,
            charter_start_date=today - timedelta(days=200),
            charter_end_date=today - timedelta(days=10)
        )
        assert ship.is_charter_active is False

    def test_is_charter_active_false_future(self):
        """Test is_charter_active when charter is in future"""
        today = date.today()
        ship = Ship.objects.create(
            imo_number='IMO4444444',
            vessel_name='Future Charter',
            vessel_type='LR1',
            built_year=2019,
            deadweight=Decimal('75000.00'),
            is_tc_fleet=True,
            charter_start_date=today + timedelta(days=10),
            charter_end_date=today + timedelta(days=100)
        )
        assert ship.is_charter_active is False

    def test_charter_days_remaining(self, tc_ship):
        """Test charter_days_remaining calculation"""
        today = date.today()
        expected_days = (tc_ship.charter_end_date - today).days
        assert tc_ship.charter_days_remaining == expected_days

    def test_charter_days_remaining_zero_when_inactive(self, basic_ship):
        """Test charter_days_remaining is 0 when not active"""
        assert basic_ship.charter_days_remaining == 0

    def test_charter_days_remaining_zero_when_expired(self):
        """Test charter_days_remaining is 0 when expired"""
        today = date.today()
        ship = Ship.objects.create(
            imo_number='IMO5555555',
            vessel_name='Expired Days Test',
            vessel_type='LR2',
            built_year=2016,
            deadweight=Decimal('110000.00'),
            is_tc_fleet=True,
            charter_start_date=today - timedelta(days=200),
            charter_end_date=today - timedelta(days=1)
        )
        assert ship.charter_days_remaining == 0

    def test_optional_fields(self):
        """Test that optional fields can be blank/null"""
        ship = Ship.objects.create(
            imo_number='IMO6666666',
            vessel_name='Minimal Ship',
            vessel_type='HANDYSIZE',
            built_year=2005,
            deadweight=Decimal('30000.00')
        )
        assert ship.flag == ''
        assert ship.gross_tonnage is None
        assert ship.engine_type == ''
        assert ship.engine_power is None
        assert ship.cargo_capacity is None

    def test_ordering(self):
        """Test default ordering by vessel_name"""
        Ship.objects.create(
            imo_number='IMO7777777',
            vessel_name='Zulu Ship',
            vessel_type='VLCC',
            built_year=2020,
            deadweight=Decimal('300000.00')
        )
        Ship.objects.create(
            imo_number='IMO8888888',
            vessel_name='Alpha Ship',
            vessel_type='AFRAMAX',
            built_year=2018,
            deadweight=Decimal('105000.00')
        )
        ships = list(Ship.objects.all())
        assert ships[0].vessel_name == 'Alpha Ship'


@pytest.mark.django_db
class TestTCFleetModel:
    """Test TCFleet model functionality"""

    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='tcuser',
            email='tc@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def active_tc_contract(self, test_user):
        """Create an active TC contract"""
        today = date.today()
        return TCFleet.objects.create(
            ship_name='Active TC Ship',
            imo_number='IMO1111111',
            ship_type='AFRAMAX',
            delivery_status='ON_TC',
            trade='CRUDE',
            owner_name='Test Owner',
            charter_length_years=Decimal('3.0'),
            tc_rate_monthly=Decimal('750000.00'),
            radar_deal_number='A1234567',
            delivery_date=today - timedelta(days=365),
            redelivery_date=today + timedelta(days=730),
            tcp_date=today - timedelta(days=400),
            summer_dwt=Decimal('105000.00'),
            built_year=2015,
            flag='Panama',
            created_by=test_user
        )

    @pytest.fixture
    def expiring_soon_contract(self, test_user):
        """Create a contract expiring soon"""
        today = date.today()
        return TCFleet.objects.create(
            ship_name='Expiring Ship',
            imo_number='IMO2222222',
            ship_type='SUEZMAX',
            delivery_status='ON_TC',
            trade='PRODUCTS',
            owner_name='Owner Two',
            charter_length_years=Decimal('2.0'),
            tc_rate_monthly=Decimal('900000.00'),
            radar_deal_number='A2345678',
            delivery_date=today - timedelta(days=700),
            redelivery_date=today + timedelta(days=20),
            tcp_date=today - timedelta(days=730),
            summer_dwt=Decimal('158000.00'),
            built_year=2018,
            flag='Liberia',
            created_by=test_user
        )

    @pytest.fixture
    def redelivered_contract(self, test_user):
        """Create a redelivered contract"""
        today = date.today()
        return TCFleet.objects.create(
            ship_name='Redelivered Ship',
            imo_number='IMO3333333',
            ship_type='VLCC',
            delivery_status='REDELIVERED',
            trade='CRUDE',
            owner_name='Owner Three',
            charter_length_years=Decimal('5.0'),
            tc_rate_monthly=Decimal('1200000.00'),
            radar_deal_number='A3456789',
            delivery_date=today - timedelta(days=1825),
            redelivery_date=today - timedelta(days=1),
            tcp_date=today - timedelta(days=1900),
            summer_dwt=Decimal('300000.00'),
            built_year=2010,
            flag='Marshall Islands',
            created_by=test_user
        )

    def test_tc_fleet_creation(self, active_tc_contract):
        """Test TC fleet contract creation"""
        assert active_tc_contract.ship_name == 'Active TC Ship'
        assert active_tc_contract.imo_number == 'IMO1111111'
        assert active_tc_contract.delivery_status == 'ON_TC'
        assert active_tc_contract.charter_length_years == Decimal('3.0')

    def test_tc_fleet_str_representation(self, active_tc_contract):
        """Test TC fleet string representation"""
        expected = "Active TC Ship (IMO: IMO1111111) - A1234567"
        assert str(active_tc_contract) == expected

    def test_radar_deal_number_uniqueness(self, active_tc_contract):
        """Test that RADAR deal numbers must be unique"""
        with pytest.raises(IntegrityError):
            TCFleet.objects.create(
                ship_name='Duplicate Deal',
                imo_number='IMO9999999',
                ship_type='PANAMAX',
                delivery_status='ON_TC',
                trade='CRUDE',
                owner_name='Test',
                charter_length_years=Decimal('1.0'),
                tc_rate_monthly=Decimal('500000.00'),
                radar_deal_number='A1234567',  # Duplicate
                delivery_date=date.today(),
                redelivery_date=date.today() + timedelta(days=365),
                tcp_date=date.today(),
                summer_dwt=Decimal('75000.00'),
                built_year=2020,
                flag='Cyprus'
            )

    def test_contract_status_active(self, active_tc_contract):
        """Test contract_status property for active contract"""
        assert active_tc_contract.contract_status == 'ACTIVE'

    def test_contract_status_expiring_soon(self, expiring_soon_contract):
        """Test contract_status for contract expiring soon"""
        assert expiring_soon_contract.contract_status == 'EXPIRING_SOON'

    def test_contract_status_redelivered(self, redelivered_contract):
        """Test contract_status for redelivered contract"""
        assert redelivered_contract.contract_status == 'COMPLETED'

    def test_contract_status_expired(self, test_user):
        """Test contract_status for expired contract"""
        today = date.today()
        contract = TCFleet.objects.create(
            ship_name='Expired Ship',
            imo_number='IMO4444444',
            ship_type='MR',
            delivery_status='ON_TC',
            trade='PRODUCTS',
            owner_name='Owner Four',
            charter_length_years=Decimal('1.0'),
            tc_rate_monthly=Decimal('600000.00'),
            radar_deal_number='A4567890',
            delivery_date=today - timedelta(days=400),
            redelivery_date=today - timedelta(days=10),
            tcp_date=today - timedelta(days=420),
            summer_dwt=Decimal('50000.00'),
            built_year=2012,
            flag='Singapore',
            created_by=test_user
        )
        assert contract.contract_status == 'EXPIRED'

    def test_contract_status_incoming(self, test_user):
        """Test contract_status for incoming contract"""
        today = date.today()
        contract = TCFleet.objects.create(
            ship_name='Incoming Ship',
            imo_number='IMO5555555',
            ship_type='LR1',
            delivery_status='INCOMING_TC',
            trade='PRODUCTS',
            owner_name='Owner Five',
            charter_length_years=Decimal('2.0'),
            tc_rate_monthly=Decimal('700000.00'),
            radar_deal_number='A5678901',
            delivery_date=today + timedelta(days=30),
            redelivery_date=today + timedelta(days=760),
            tcp_date=today - timedelta(days=10),
            summer_dwt=Decimal('75000.00'),
            built_year=2019,
            flag='Hong Kong',
            created_by=test_user
        )
        assert contract.contract_status == 'INCOMING'

    def test_days_remaining(self, active_tc_contract):
        """Test days_remaining calculation"""
        today = date.today()
        expected = (active_tc_contract.redelivery_date - today).days
        assert active_tc_contract.days_remaining == expected

    def test_days_remaining_redelivered(self, redelivered_contract):
        """Test days_remaining is 0 for redelivered contract"""
        assert redelivered_contract.days_remaining == 0

    def test_charter_length_months(self, active_tc_contract):
        """Test charter_length_months calculation"""
        expected = 3.0 * 12
        assert active_tc_contract.charter_length_months == expected

    def test_total_contract_value(self, active_tc_contract):
        """Test total_contract_value calculation"""
        expected = Decimal('750000.00') * Decimal('36')  # 3 years * 12 months
        assert active_tc_contract.total_contract_value == expected

    def test_charter_length_months_fractional(self, test_user):
        """Test charter_length_months with fractional years"""
        contract = TCFleet.objects.create(
            ship_name='Fractional Charter',
            imo_number='IMO6666666',
            ship_type='LR2',
            delivery_status='ON_TC',
            trade='PRODUCTS',
            owner_name='Owner Six',
            charter_length_years=Decimal('1.5'),
            tc_rate_monthly=Decimal('800000.00'),
            radar_deal_number='A6789012',
            delivery_date=date.today(),
            redelivery_date=date.today() + timedelta(days=547),
            tcp_date=date.today(),
            summer_dwt=Decimal('110000.00'),
            built_year=2017,
            flag='Malta',
            created_by=test_user
        )
        assert contract.charter_length_months == 18.0
        assert contract.total_contract_value == Decimal('800000.00') * Decimal('18')

    def test_optional_fields(self, test_user):
        """Test that optional fields can be blank/null"""
        contract = TCFleet.objects.create(
            ship_name='Minimal Contract',
            imo_number='IMO7777777',
            ship_type='HANDYSIZE',
            delivery_status='ON_TC',
            trade='CHEMICAL',
            owner_name='Minimal Owner',
            charter_length_years=Decimal('1.0'),
            tc_rate_monthly=Decimal('400000.00'),
            radar_deal_number='A7890123',
            delivery_date=date.today(),
            redelivery_date=date.today() + timedelta(days=365),
            tcp_date=date.today(),
            summer_dwt=Decimal('35000.00'),
            built_year=2015,
            flag='UK',
            created_by=test_user
        )
        assert contract.owner_email == ''
        assert contract.technical_manager == ''
        assert contract.broker_name == ''
        assert contract.broker_commission is None
        assert contract.next_drydock_date is None


@pytest.mark.django_db
class TestShipSpecificationModel:
    """Test ShipSpecification (Q88) model functionality"""

    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='q88user',
            email='q88@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def basic_q88(self, test_user):
        """Create a basic Q88 specification"""
        return ShipSpecification.objects.create(
            vessel_name='Q88 Test Vessel',
            imo_number='IMO9999999',
            flag='Panama',
            vessel_type='CRUDE',
            built_year=2015,
            length_overall=Decimal('250.00'),
            breadth_moulded=Decimal('44.00'),
            depth_moulded=Decimal('21.00'),
            summer_draft=Decimal('16.50'),
            summer_deadweight=Decimal('105000.00'),
            lightweight=Decimal('15000.00'),
            gross_tonnage=Decimal('60000.00'),
            net_tonnage=Decimal('35000.00'),
            total_cargo_capacity=Decimal('120000.00'),
            number_of_cargo_tanks=12,
            cargo_tank_coating='EPOXY',
            main_engine_type='MAN B&W 6S50MC-C',
            main_engine_power=Decimal('9480.00'),
            service_speed_laden=Decimal('14.5'),
            service_speed_ballast=Decimal('15.0'),
            fuel_consumption_laden=Decimal('35.0'),
            fuel_consumption_ballast=Decimal('30.0'),
            fuel_type='IFO',
            number_of_cargo_pumps=3,
            cargo_pump_capacity=Decimal('2400.00'),
            cargo_manifold_size=Decimal('16.0'),
            owner_name='Q88 Owner',
            technical_manager='Q88 Tech Manager',
            created_by=test_user
        )

    def test_q88_creation(self, basic_q88):
        """Test Q88 specification creation"""
        assert basic_q88.vessel_name == 'Q88 Test Vessel'
        assert basic_q88.imo_number == 'IMO9999999'
        assert basic_q88.vessel_type == 'CRUDE'
        assert basic_q88.number_of_cargo_tanks == 12

    def test_q88_str_representation(self, basic_q88):
        """Test Q88 string representation"""
        expected = "Q88 Test Vessel (IMO9999999)"
        assert str(basic_q88) == expected

    def test_imo_number_uniqueness_q88(self, basic_q88):
        """Test that IMO numbers must be unique in Q88"""
        with pytest.raises(IntegrityError):
            ShipSpecification.objects.create(
                vessel_name='Duplicate Q88',
                imo_number='IMO9999999',  # Duplicate
                flag='Liberia',
                vessel_type='PRODUCT',
                built_year=2018,
                length_overall=Decimal('230.00'),
                breadth_moulded=Decimal('42.00'),
                depth_moulded=Decimal('20.00'),
                summer_draft=Decimal('15.00'),
                summer_deadweight=Decimal('95000.00'),
                lightweight=Decimal('14000.00'),
                gross_tonnage=Decimal('55000.00'),
                net_tonnage=Decimal('32000.00'),
                total_cargo_capacity=Decimal('110000.00'),
                number_of_cargo_tanks=10,
                cargo_tank_coating='ZINC',
                main_engine_type='Test Engine',
                main_engine_power=Decimal('8000.00'),
                service_speed_laden=Decimal('14.0'),
                service_speed_ballast=Decimal('14.5'),
                fuel_consumption_laden=Decimal('32.0'),
                fuel_consumption_ballast=Decimal('28.0'),
                fuel_type='MGO',
                number_of_cargo_pumps=3,
                cargo_pump_capacity=Decimal('2200.00'),
                cargo_manifold_size=Decimal('14.0'),
                owner_name='Test Owner',
                technical_manager='Test Manager'
            )

    def test_displacement_property(self, basic_q88):
        """Test displacement calculation"""
        expected = Decimal('105000.00') + Decimal('15000.00')
        assert basic_q88.displacement == expected

    def test_cargo_capacity_per_tank(self, basic_q88):
        """Test cargo capacity per tank calculation"""
        expected = Decimal('120000.00') / 12
        assert basic_q88.cargo_capacity_per_tank == expected

    def test_cargo_capacity_per_tank_zero_tanks(self, test_user):
        """Test cargo capacity per tank when no tanks"""
        q88 = ShipSpecification.objects.create(
            vessel_name='No Tanks Ship',
            imo_number='IMO8888888',
            flag='Cyprus',
            vessel_type='CHEMICAL',
            built_year=2020,
            length_overall=Decimal('180.00'),
            breadth_moulded=Decimal('32.00'),
            depth_moulded=Decimal('18.00'),
            summer_draft=Decimal('12.00'),
            summer_deadweight=Decimal('45000.00'),
            lightweight=Decimal('8000.00'),
            gross_tonnage=Decimal('28000.00'),
            net_tonnage=Decimal('16000.00'),
            total_cargo_capacity=Decimal('50000.00'),
            number_of_cargo_tanks=0,
            cargo_tank_coating='STAINLESS_STEEL',
            main_engine_type='Test',
            main_engine_power=Decimal('6000.00'),
            service_speed_laden=Decimal('13.0'),
            service_speed_ballast=Decimal('13.5'),
            fuel_consumption_laden=Decimal('25.0'),
            fuel_consumption_ballast=Decimal('22.0'),
            fuel_type='MGO',
            number_of_cargo_pumps=2,
            cargo_pump_capacity=Decimal('1800.00'),
            cargo_manifold_size=Decimal('12.0'),
            owner_name='Owner',
            technical_manager='Manager',
            created_by=test_user
        )
        assert q88.cargo_capacity_per_tank == 0

    def test_boolean_fields_defaults(self, basic_q88):
        """Test boolean field defaults"""
        assert basic_q88.cargo_heating_capability is False
        assert basic_q88.bow_thruster is False
        assert basic_q88.stern_thruster is False
        assert basic_q88.inert_gas_system is False
        assert basic_q88.crude_oil_washing is False
        assert basic_q88.vapor_recovery_system is False
        assert basic_q88.double_hull is True  # Default True


@pytest.mark.django_db
class TestCrossAppIntegration:
    """Test cross-app integration methods"""

    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='integration_user',
            email='integration@example.com',
            password='testpass123',
            role='WRITE'
        )

    @pytest.fixture
    def ship_with_master_data(self):
        """Create a ship in Ship model"""
        return Ship.objects.create(
            imo_number='IMO1234TEST',
            vessel_name='Integration Test Ship',
            vessel_type='AFRAMAX',
            built_year=2015,
            deadweight=Decimal('105000.00')
        )

    @pytest.fixture
    def tc_contract_for_ship(self, ship_with_master_data, test_user):
        """Create a TC contract for the ship"""
        today = date.today()
        return TCFleet.objects.create(
            ship_name=ship_with_master_data.vessel_name,
            imo_number=ship_with_master_data.imo_number,
            ship_type='AFRAMAX',
            delivery_status='ON_TC',
            trade='CRUDE',
            owner_name='Integration Owner',
            charter_length_years=Decimal('2.0'),
            tc_rate_monthly=Decimal('700000.00'),
            radar_deal_number='INT123456',
            delivery_date=today - timedelta(days=200),
            redelivery_date=today + timedelta(days=530),
            tcp_date=today - timedelta(days=220),
            summer_dwt=ship_with_master_data.deadweight,
            built_year=ship_with_master_data.built_year,
            flag='Panama',
            created_by=test_user
        )

    def test_tc_fleet_get_ship_master_data(
        self, ship_with_master_data, tc_contract_for_ship
    ):
        """Test getting ship master data from TC contract"""
        ship = tc_contract_for_ship.get_ship_master_data()
        assert ship is not None
        assert ship.imo_number == ship_with_master_data.imo_number
        assert ship.vessel_name == ship_with_master_data.vessel_name

    def test_tc_fleet_get_ship_master_data_not_exists(self, test_user):
        """Test getting ship master data when it doesn't exist"""
        today = date.today()
        contract = TCFleet.objects.create(
            ship_name='No Master Data Ship',
            imo_number='IMONOMASTER',
            ship_type='PANAMAX',
            delivery_status='ON_TC',
            trade='PRODUCTS',
            owner_name='Test',
            charter_length_years=Decimal('1.0'),
            tc_rate_monthly=Decimal('500000.00'),
            radar_deal_number='NOMASTER1',
            delivery_date=today,
            redelivery_date=today + timedelta(days=365),
            tcp_date=today,
            summer_dwt=Decimal('75000.00'),
            built_year=2020,
            flag='Cyprus',
            created_by=test_user
        )
        ship = contract.get_ship_master_data()
        assert ship is None

    def test_tc_fleet_get_contract_history_for_ship(
        self, ship_with_master_data, tc_contract_for_ship, test_user
    ):
        """Test getting contract history for a ship"""
        # Create another contract for same ship
        today = date.today()
        TCFleet.objects.create(
            ship_name=ship_with_master_data.vessel_name,
            imo_number=ship_with_master_data.imo_number,
            ship_type='AFRAMAX',
            delivery_status='REDELIVERED',
            trade='CRUDE',
            owner_name='Previous Owner',
            charter_length_years=Decimal('1.0'),
            tc_rate_monthly=Decimal('600000.00'),
            radar_deal_number='PREV12345',
            delivery_date=today - timedelta(days=800),
            redelivery_date=today - timedelta(days=435),
            tcp_date=today - timedelta(days=820),
            summer_dwt=Decimal('105000.00'),
            built_year=2015,
            flag='Liberia',
            created_by=test_user
        )

        history = tc_contract_for_ship.get_contract_history_for_ship()
        assert history.count() == 2
        assert history.first() == tc_contract_for_ship  # Most recent first
