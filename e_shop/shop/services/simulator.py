from decimal import Decimal
from shop.models import OrderImpact

# Simple projection: use average of last N orders, apply reduction_target (%), and project months_ahead

def average_recent_carbon(user, orders_count=3):
    qs = OrderImpact.objects.filter(order__user=user).order_by('-created_at')[:orders_count]
    totals = [oi.carbon_kg for oi in qs]
    if not totals:
        return Decimal('0')
    return sum(totals) / len(totals)


def project_scenario(user, swap_fraction: Decimal, saving_ratio: Decimal, months: int):
    base_monthly = average_recent_carbon(user)
    # effective reduction = swap_fraction * saving_ratio
    reduction_factor = swap_fraction * saving_ratio
    if reduction_factor > 1:
        reduction_factor = Decimal('1')
    projected_monthly = base_monthly * (Decimal('1') - reduction_factor)
    total_base = base_monthly * months
    total_projected = projected_monthly * months
    total_saved = total_base - total_projected
    if total_saved < 0:
        total_saved = Decimal('0')
    return {
        'base_monthly': round(base_monthly, 2),
        'projected_monthly': round(projected_monthly, 2),
        'months': months,
        'total_base': round(total_base, 2),
        'total_projected': round(total_projected, 2),
        'total_saved': round(total_saved, 2),
        'reduction_factor': float(reduction_factor),
    }
