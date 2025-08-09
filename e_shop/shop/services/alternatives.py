from shop.models import Product


def greener_alternative(product: Product):
    return (
        Product.objects.filter(category=product.category, available=True)
        .exclude(id=product.id)
        .order_by('carbon_footprint_kg', 'id')
        .first()
    )


def swap_ladder(product: Product):
    qs = Product.objects.filter(category=product.category, available=True).order_by('carbon_footprint_kg', 'id')
    items = list(qs)
    current = product
    better = None
    best = items[0] if items else None
    for p in items:
        if p.effective_carbon_kg() < current.effective_carbon_kg():
            better = p
            break
    return {
        'current': current,
        'better': better,
        'best': best if best and best.id != current.id else (better or best)
    }
