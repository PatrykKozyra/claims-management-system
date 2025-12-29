from django.core.management.base import BaseCommand
from port_activities.models import ActivityType


class Command(BaseCommand):
    help = 'Populate Activity Types for Port Activities'

    ACTIVITY_TYPES = [
        # CARGO OPERATIONS
        ('load', 'Loading Cargo', 'CARGO_OPS', 'Loading cargo operations', 'bi-box-seam-fill', 'primary'),
        ('discharge', 'Discharging Cargo', 'CARGO_OPS', 'Discharging cargo operations', 'bi-box-arrow-down', 'success'),
        ('part_load', 'Partial Loading', 'CARGO_OPS', 'Partial loading operations', 'bi-box-seam', 'info'),
        ('part_discharge', 'Partial Discharging', 'CARGO_OPS', 'Partial discharging operations', 'bi-box-arrow-in-down', 'info'),
        ('topping_off', 'Topping Off', 'CARGO_OPS', 'Final loading to capacity', 'bi-arrow-up-circle', 'primary'),
        ('ship_to_ship_transfer', 'Ship-to-Ship Transfer (STS)', 'CARGO_OPS', 'STS cargo transfer operation', 'bi-arrow-left-right', 'warning'),
        ('lightering', 'Lightering', 'CARGO_OPS', 'Transferring cargo to smaller vessel', 'bi-share', 'warning'),

        # BALLASTING OPERATIONS
        ('ballasting', 'Ballasting', 'BALLASTING', 'Taking on ballast water', 'bi-droplet-fill', 'info'),
        ('deballasting', 'Deballasting', 'BALLASTING', 'Discharging ballast water', 'bi-droplet-half', 'info'),
        ('ballast_exchange', 'Ballast Exchange', 'BALLASTING', 'Ocean ballast water exchange', 'bi-arrow-repeat', 'info'),

        # CLEANING & PREPARATION
        ('tank_cleaning', 'Tank Cleaning', 'CLEANING', 'Cargo tank cleaning', 'bi-droplet', 'secondary'),
        ('tank_washing', 'Tank Washing', 'CLEANING', 'Tank washing operations', 'bi-droplet', 'secondary'),
        ('crude_oil_washing', 'Crude Oil Washing (COW)', 'CLEANING', 'Crude oil washing system operation', 'bi-droplet-fill', 'dark'),
        ('gas_freeing', 'Gas Freeing', 'CLEANING', 'Removing cargo vapors from tanks', 'bi-wind', 'secondary'),
        ('tank_inspection', 'Tank Inspection', 'CLEANING', 'Internal tank inspection', 'bi-search', 'secondary'),
        ('line_blowing', 'Line Blowing', 'CLEANING', 'Clearing cargo lines with air', 'bi-wind', 'secondary'),
        ('stripping', 'Stripping', 'CLEANING', 'Removing last traces of cargo', 'bi-droplet-half', 'secondary'),

        # BUNKERING & SUPPLIES
        ('bunkering', 'Bunkering', 'BUNKERING', 'Taking on fuel', 'bi-fuel-pump-fill', 'warning'),
        ('freshwater_supply', 'Freshwater Supply', 'BUNKERING', 'Loading freshwater', 'bi-water', 'info'),
        ('provisions_supply', 'Provisions Supply', 'BUNKERING', 'Loading food and supplies', 'bi-cart-fill', 'success'),
        ('lube_oil_supply', 'Lube Oil Supply', 'BUNKERING', 'Loading lubricating oil', 'bi-droplet-fill', 'warning'),
        ('debunkering', 'Debunkering', 'BUNKERING', 'Removing fuel or slops', 'bi-fuel-pump', 'danger'),

        # MAINTENANCE & REPAIRS
        ('drydocking', 'Drydocking', 'MAINTENANCE', 'Vessel in drydock for repairs', 'bi-tools', 'danger'),
        ('repairs', 'Repairs', 'MAINTENANCE', 'Repair works', 'bi-wrench-adjustable', 'warning'),
        ('maintenance', 'Maintenance', 'MAINTENANCE', 'Routine maintenance', 'bi-gear-fill', 'secondary'),
        ('underwater_inspection', 'Underwater Inspection', 'MAINTENANCE', 'Underwater hull inspection', 'bi-search', 'info'),
        ('surveys', 'Surveys', 'MAINTENANCE', 'Class surveys and annual surveys', 'bi-clipboard-check', 'primary'),
        ('coating_works', 'Coating Works', 'MAINTENANCE', 'Hull or tank coating application', 'bi-brush', 'secondary'),

        # OPERATIONAL STATUS
        ('waiting_for_berth', 'Waiting for Berth', 'OPERATIONAL', 'Waiting for berth availability', 'bi-pause-circle', 'warning'),
        ('waiting_for_orders', 'Waiting for Orders', 'OPERATIONAL', 'Awaiting instructions', 'bi-hourglass-split', 'warning'),
        ('waiting_for_load_port', 'Waiting for Load Port', 'OPERATIONAL', 'En route to load port', 'bi-hourglass', 'warning'),
        ('waiting_for_discharge_port', 'Waiting for Discharge Port', 'OPERATIONAL', 'En route to discharge port', 'bi-hourglass', 'warning'),
        ('at_anchorage', 'At Anchorage', 'OPERATIONAL', 'Vessel anchored', 'bi-pin-map', 'secondary'),
        ('drifting', 'Drifting', 'OPERATIONAL', 'Vessel drifting', 'bi-wind', 'secondary'),
        ('deviation', 'Deviation', 'OPERATIONAL', 'Off planned route', 'bi-exclamation-triangle', 'warning'),
        ('weather_delay', 'Weather Delay', 'OPERATIONAL', 'Delayed due to weather', 'bi-cloud-drizzle', 'danger'),
        ('force_majeure', 'Force Majeure', 'OPERATIONAL', 'Force majeure event', 'bi-exclamation-octagon', 'danger'),

        # ADMINISTRATIVE & COMPLIANCE
        ('customs_clearance', 'Customs Clearance', 'ADMINISTRATIVE', 'Customs formalities', 'bi-file-earmark-check', 'primary'),
        ('port_state_control_inspection', 'Port State Control Inspection', 'ADMINISTRATIVE', 'PSC inspection', 'bi-clipboard-check', 'warning'),
        ('quarantine_inspection', 'Quarantine Inspection', 'ADMINISTRATIVE', 'Health quarantine inspection', 'bi-clipboard-plus', 'warning'),
        ('immigration_clearance', 'Immigration Clearance', 'ADMINISTRATIVE', 'Crew immigration processing', 'bi-person-check', 'primary'),
        ('fumigation', 'Fumigation', 'ADMINISTRATIVE', 'Cargo or vessel fumigation', 'bi-bug', 'danger'),
        ('cargo_sampling', 'Cargo Sampling', 'ADMINISTRATIVE', 'Taking cargo samples', 'bi-eyedropper', 'info'),
        ('cargo_inspection', 'Cargo Inspection', 'ADMINISTRATIVE', 'Cargo quality inspection', 'bi-search', 'info'),
        ('draught_survey', 'Draught Survey', 'ADMINISTRATIVE', 'Vessel draft measurement', 'bi-rulers', 'primary'),
        ('vetting_inspection', 'Vetting Inspection', 'ADMINISTRATIVE', 'SIRE or other vetting inspection', 'bi-clipboard-data', 'warning'),

        # OFF-HIRE EVENTS
        ('offhire_breakdown', 'Off-hire: Breakdown', 'OFFHIRE', 'Mechanical failure causing off-hire', 'bi-x-octagon', 'danger'),
        ('offhire_deviation', 'Off-hire: Deviation', 'OFFHIRE', 'Deviation causing off-hire', 'bi-x-circle', 'danger'),
        ('offhire_repairs', 'Off-hire: Repairs', 'OFFHIRE', 'Repairs causing off-hire', 'bi-x-circle', 'danger'),
        ('offhire_speed_deficiency', 'Off-hire: Speed Deficiency', 'OFFHIRE', 'Insufficient speed causing off-hire', 'bi-speedometer', 'danger'),
        ('offhire_crew_issue', 'Off-hire: Crew Issue', 'OFFHIRE', 'Crew-related off-hire', 'bi-people', 'danger'),

        # TRANSIT & NAVIGATION
        ('in_transit', 'In Transit', 'TRANSIT', 'Vessel in transit between ports', 'bi-arrow-right-circle', 'success'),
        ('canal_transit', 'Canal Transit', 'TRANSIT', 'Transiting Suez/Panama Canal', 'bi-water', 'primary'),
        ('pilot_onboard', 'Pilot Onboard', 'TRANSIT', 'Pilot embarked for navigation', 'bi-person-badge', 'info'),
        ('shifting_berth', 'Shifting Berth', 'TRANSIT', 'Moving between berths', 'bi-arrows-move', 'info'),
        ('berthing', 'Berthing', 'TRANSIT', 'Berthing operation', 'bi-arrow-down-square', 'success'),
        ('unberthing', 'Unberthing', 'TRANSIT', 'Unberthing operation', 'bi-arrow-up-square', 'primary'),

        # COMMERCIAL ACTIVITIES
        ('redelivery', 'Redelivery', 'COMMERCIAL', 'End of time charter period', 'bi-box-arrow-left', 'danger'),
        ('delivery', 'Delivery', 'COMMERCIAL', 'Start of time charter period', 'bi-box-arrow-in-right', 'success'),
        ('lay_up', 'Lay-up', 'COMMERCIAL', 'Vessel inactive/laid up', 'bi-pause-circle-fill', 'secondary'),
        ('warm_lay_up', 'Warm Lay-up', 'COMMERCIAL', 'Vessel inactive but maintained', 'bi-pause-circle', 'warning'),
        ('scrapping', 'Scrapping', 'COMMERCIAL', 'Vessel being scrapped', 'bi-trash', 'danger'),
    ]

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating Activity Types...')

        created_count = 0
        updated_count = 0

        for code, name, category, description, icon_class, color_class in self.ACTIVITY_TYPES:
            activity_type, created = ActivityType.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': category,
                    'description': description,
                    'icon_class': icon_class,
                    'color_class': color_class,
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  Created: {name} ({code})')
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {name} ({code})')

        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted: {created_count} created, {updated_count} updated'
        ))
        self.stdout.write(self.style.SUCCESS(f'Total activity types: {ActivityType.objects.count()}'))
