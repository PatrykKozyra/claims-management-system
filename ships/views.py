from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg
from django.http import HttpResponse
from decimal import Decimal
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime

from .models import TCFleet, Ship


@login_required
def tc_fleet_list(request):
    """
    Display list of TC Fleet contracts with filters.
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    ship_type_filter = request.GET.get('ship_type', '')
    trade_filter = request.GET.get('trade', '')
    owner_filter = request.GET.get('owner', '')
    trader_filter = request.GET.get('trader', '')
    search_query = request.GET.get('search', '')

    # Base queryset
    contracts = TCFleet.objects.all().select_related('created_by')

    # Apply filters
    if status_filter:
        contracts = contracts.filter(delivery_status=status_filter)
    if ship_type_filter:
        contracts = contracts.filter(ship_type=ship_type_filter)
    if trade_filter:
        contracts = contracts.filter(trade=trade_filter)
    if owner_filter:
        contracts = contracts.filter(owner_name=owner_filter)
    if trader_filter:
        contracts = contracts.filter(trader_name=trader_filter)
    if search_query:
        contracts = contracts.filter(
            Q(ship_name__icontains=search_query) |
            Q(imo_number__icontains=search_query) |
            Q(radar_deal_number__icontains=search_query) |
            Q(owner_name__icontains=search_query)
        )

    # Get unique values for filter dropdowns
    ship_types = TCFleet.objects.values_list('ship_type', flat=True).distinct().order_by('ship_type')
    trades = TCFleet.objects.values_list('trade', flat=True).distinct().order_by('trade')
    owners = TCFleet.objects.values_list('owner_name', flat=True).distinct().order_by('owner_name')
    traders = TCFleet.objects.filter(trader_name__isnull=False).exclude(trader_name='').values_list('trader_name', flat=True).distinct().order_by('trader_name')

    # Calculate statistics
    total_contracts = contracts.count()
    active_contracts = contracts.filter(delivery_status='ON_TC').count()
    incoming_contracts = contracts.filter(delivery_status='INCOMING_TC').count()
    redelivered_contracts = contracts.filter(delivery_status='REDELIVERED').count()

    context = {
        'contracts': contracts,
        'ship_types': ship_types,
        'trades': trades,
        'owners': owners,
        'traders': traders,
        'status_filter': status_filter,
        'ship_type_filter': ship_type_filter,
        'trade_filter': trade_filter,
        'owner_filter': owner_filter,
        'trader_filter': trader_filter,
        'search_query': search_query,
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'incoming_contracts': incoming_contracts,
        'redelivered_contracts': redelivered_contracts,
    }

    return render(request, 'ships/tc_fleet_list.html', context)


@login_required
def tc_fleet_detail(request, pk):
    """
    Display detailed view of a single TC Fleet contract.
    """
    contract = get_object_or_404(TCFleet, pk=pk)

    # Get all contracts for the same ship (IMO)
    contract_history = TCFleet.objects.filter(
        imo_number=contract.imo_number
    ).exclude(pk=pk).order_by('-delivery_date')

    # Get ship master data if exists
    ship_master = contract.get_ship_master_data()

    context = {
        'contract': contract,
        'contract_history': contract_history,
        'ship_master': ship_master,
    }

    return render(request, 'ships/tc_fleet_detail.html', context)


@login_required
def tc_fleet_by_ship(request, imo_number):
    """
    Display all TC Fleet contracts for a specific ship (by IMO number).
    Shows contract history timeline.
    """
    # Get all contracts for this IMO
    contracts = TCFleet.objects.filter(
        imo_number=imo_number
    ).order_by('-delivery_date')

    if not contracts.exists():
        return redirect('ships:tc_fleet_list')

    # Get ship master data if exists
    ship_master = None
    try:
        ship_master = Ship.objects.get(imo_number=imo_number)
    except Ship.DoesNotExist:
        pass

    # Get the most recent contract for ship name
    latest_contract = contracts.first()

    # Calculate statistics for this ship
    total_contracts = contracts.count()
    active_contracts = contracts.filter(delivery_status='ON_TC').count()
    redelivered_contracts = contracts.filter(delivery_status='REDELIVERED').count()

    context = {
        'contracts': contracts,
        'imo_number': imo_number,
        'ship_name': latest_contract.ship_name,
        'ship_master': ship_master,
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'redelivered_contracts': redelivered_contracts,
    }

    return render(request, 'ships/tc_fleet_by_ship.html', context)


@login_required
def tc_fleet_export(request):
    """
    Export TC Fleet contracts to Excel.
    Applies the same filters as the list view.
    """
    # Check if user has export permission
    if not request.user.can_export():
        return redirect('ships:tc_fleet_list')

    # Get filter parameters (same as list view)
    status_filter = request.GET.get('status', '')
    ship_type_filter = request.GET.get('ship_type', '')
    trade_filter = request.GET.get('trade', '')
    owner_filter = request.GET.get('owner', '')
    trader_filter = request.GET.get('trader', '')
    search_query = request.GET.get('search', '')

    # Base queryset
    contracts = TCFleet.objects.all().select_related('created_by')

    # Apply filters
    if status_filter:
        contracts = contracts.filter(delivery_status=status_filter)
    if ship_type_filter:
        contracts = contracts.filter(ship_type=ship_type_filter)
    if trade_filter:
        contracts = contracts.filter(trade=trade_filter)
    if owner_filter:
        contracts = contracts.filter(owner_name=owner_filter)
    if trader_filter:
        contracts = contracts.filter(trader_name=trader_filter)
    if search_query:
        contracts = contracts.filter(
            Q(ship_name__icontains=search_query) |
            Q(imo_number__icontains=search_query) |
            Q(radar_deal_number__icontains=search_query) |
            Q(owner_name__icontains=search_query)
        )

    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TC Fleet Contracts"

    # Define headers
    headers = [
        'Ship Name', 'IMO Number', 'Ship Type', 'Delivery Status', 'Trade',
        'Owner Name', 'Owner Email', 'Technical Manager', 'Tech Manager Email',
        'Charter Length (Years)', 'TC Rate Monthly (USD)', 'RADAR Deal Number',
        'Delivery Date', 'Redelivery Date', 'TCP Date', 'Broker Name',
        'Broker Email', 'Broker Commission (%)', 'Delivery Location',
        'Redelivery Location', 'Bunkers Policy', 'Summer DWT', 'Built Year',
        'Flag', 'Next Dry-Dock Date', 'Trader Name', 'Days Remaining',
        'Contract Status', 'Total Contract Value (USD)'
    ]

    # Style for header row
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    header_alignment = Alignment(horizontal="center", vertical="center")

    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    # Write data rows
    for row_num, contract in enumerate(contracts, 2):
        ws.cell(row=row_num, column=1).value = contract.ship_name
        ws.cell(row=row_num, column=2).value = contract.imo_number
        ws.cell(row=row_num, column=3).value = contract.get_ship_type_display()
        ws.cell(row=row_num, column=4).value = contract.get_delivery_status_display()
        ws.cell(row=row_num, column=5).value = contract.get_trade_display()
        ws.cell(row=row_num, column=6).value = contract.owner_name
        ws.cell(row=row_num, column=7).value = contract.owner_email
        ws.cell(row=row_num, column=8).value = contract.technical_manager
        ws.cell(row=row_num, column=9).value = contract.technical_manager_email
        ws.cell(row=row_num, column=10).value = float(contract.charter_length_years)
        ws.cell(row=row_num, column=11).value = float(contract.tc_rate_monthly)
        ws.cell(row=row_num, column=12).value = contract.radar_deal_number
        ws.cell(row=row_num, column=13).value = contract.delivery_date.strftime('%d/%m/%Y')
        ws.cell(row=row_num, column=14).value = contract.redelivery_date.strftime('%d/%m/%Y')
        ws.cell(row=row_num, column=15).value = contract.tcp_date.strftime('%d/%m/%Y')
        ws.cell(row=row_num, column=16).value = contract.broker_name
        ws.cell(row=row_num, column=17).value = contract.broker_email
        ws.cell(row=row_num, column=18).value = float(contract.broker_commission) if contract.broker_commission else None
        ws.cell(row=row_num, column=19).value = contract.delivery_location
        ws.cell(row=row_num, column=20).value = contract.redelivery_location
        ws.cell(row=row_num, column=21).value = contract.get_bunkers_policy_display() if contract.bunkers_policy else ''
        ws.cell(row=row_num, column=22).value = float(contract.summer_dwt)
        ws.cell(row=row_num, column=23).value = contract.built_year
        ws.cell(row=row_num, column=24).value = contract.flag
        ws.cell(row=row_num, column=25).value = contract.next_drydock_date.strftime('%d/%m/%Y') if contract.next_drydock_date else ''
        ws.cell(row=row_num, column=26).value = contract.trader_name
        ws.cell(row=row_num, column=27).value = contract.days_remaining
        ws.cell(row=row_num, column=28).value = contract.contract_status
        ws.cell(row=row_num, column=29).value = float(contract.total_contract_value)

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=tc_fleet_contracts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    wb.save(response)
    return response
