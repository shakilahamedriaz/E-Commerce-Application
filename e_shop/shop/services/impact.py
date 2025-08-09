from decimal import Decimal
from shop.models import Product, OrderImpact, UserImpact, Order
from . import badges as badge_service


def category_baseline_for_product(product: Product) -> Decimal:
    qs = Product.objects.filter(category=product.category).select_related('category')
    total = Decimal('0')
    count = 0
    for p in qs.only('id', 'carbon_footprint_kg', 'category__default_emission_factor_kg'):
        total += p.effective_carbon_kg()
        count += 1
    return (total / count) if count else Decimal('0')


def compute_order_impact(order: Order):
    carbon_total = Decimal('0')
    baseline_total = Decimal('0')
    for item in order.items.select_related('product', 'product__category'):
        product = item.product
        eff = product.effective_carbon_kg()
        baseline = category_baseline_for_product(product)
        carbon_total += eff * item.quantity
        baseline_total += baseline * item.quantity
    saved = baseline_total - carbon_total
    if saved < 0:
        saved = Decimal('0')
    return carbon_total, baseline_total, saved


def update_user_impact(order: Order, carbon_total: Decimal, saved: Decimal):
    if order.user is None:
        return
    ui, _ = UserImpact.objects.get_or_create(user=order.user)
    ui.total_orders += 1
    ui.total_carbon_kg += carbon_total
    ui.total_saved_kg += saved
    ui.current_month_carbon_kg += carbon_total  # simple accumulation; monthly reset can adjust
    # streak logic: saved > 0 means below baseline
    if saved > 0:
        ui.low_impact_streak += 1
    else:
        ui.low_impact_streak = 0
    ui.save()
    # award badges after save
    try:
        badge_service.evaluate_and_award(order.user, ui, saved)
    except Exception:
        pass


def record_order_impact(order: Order):
    if hasattr(order, 'impact'):
        return order.impact
    carbon_total, baseline_total, saved = compute_order_impact(order)
    impact = OrderImpact.objects.create(
        order=order,
        carbon_kg=carbon_total,
        baseline_kg=baseline_total,
        saved_kg=saved
    )
    update_user_impact(order, carbon_total, saved)
    return impact
