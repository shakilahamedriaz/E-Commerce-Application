from decimal import Decimal
from datetime import datetime
from shop.models import UserImpact


BUDGET_STATUS_THRESHOLDS = {
    'green': Decimal('0.70'),
    'amber': Decimal('1.00'),
}

def get_or_create_user_impact(user):
    ui, _ = UserImpact.objects.get_or_create(user=user)
    return ui

def month_key(dt=None):
    dt = dt or datetime.utcnow()
    return dt.strftime('%Y-%m')

# Placeholder for month reset; future: store last_reset_month

def budget_status(user):
    ui = get_or_create_user_impact(user)
    if ui.month_budget_kg <= 0:
        return 'unset'
    ratio = Decimal('0') if ui.month_budget_kg == 0 else (ui.current_month_carbon_kg / ui.month_budget_kg)
    if ratio <= BUDGET_STATUS_THRESHOLDS['green']:
        return 'green'
    if ratio <= BUDGET_STATUS_THRESHOLDS['amber']:
        return 'amber'
    return 'red'


def update_budget(user, new_budget: Decimal):
    ui = get_or_create_user_impact(user)
    ui.month_budget_kg = new_budget
    ui.save()
    return ui
