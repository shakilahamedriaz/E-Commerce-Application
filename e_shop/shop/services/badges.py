from decimal import Decimal
from shop.models import Badge, UserBadge, UserImpact
from django.contrib.auth import get_user_model

# Predefined badge definitions (idempotent creation function)
BADGE_DEFS = [
    {"code": "FIRST_GREEN", "name": "First Low Impact", "condition_type": "FIRST_ORDER", "threshold": Decimal('0'), "description": "First order below baseline."},
    {"code": "SAVED_5", "name": "5 Kg Saved", "condition_type": "TOTAL_SAVED", "threshold": Decimal('5'), "description": "Saved 5 kg CO₂e cumulatively."},
    {"code": "SAVED_20", "name": "20 Kg Saved", "condition_type": "TOTAL_SAVED", "threshold": Decimal('20'), "description": "Saved 20 kg CO₂e cumulatively."},
    {"code": "STREAK_3", "name": "3 Streak", "condition_type": "STREAK", "threshold": Decimal('3'), "description": "3 consecutive low impact orders."},
]


def ensure_badges_seeded():
    for bd in BADGE_DEFS:
        Badge.objects.get_or_create(code=bd['code'], defaults={
            'name': bd['name'],
            'description': bd['description'],
            'condition_type': bd['condition_type'],
            'threshold': bd['threshold'],
        })


def evaluate_and_award(user, impact: UserImpact, last_saved: Decimal):
    ensure_badges_seeded()
    awarded_codes = set(UserBadge.objects.filter(user=user).values_list('badge__code', flat=True))
    # FIRST_ORDER (low impact) badge
    if 'FIRST_GREEN' not in awarded_codes and last_saved > 0:
        _award(user, 'FIRST_GREEN')
    # TOTAL_SAVED thresholds
    for code, thresh in [('SAVED_20', Decimal('20')), ('SAVED_5', Decimal('5'))]:  # evaluate higher first
        if code not in awarded_codes and impact.total_saved_kg >= thresh:
            _award(user, code)
    # STREAK
    if 'STREAK_3' not in awarded_codes and impact.low_impact_streak >= 3:
        _award(user, 'STREAK_3')


def _award(user, code: str):
    try:
        badge = Badge.objects.get(code=code)
        UserBadge.objects.create(user=user, badge=badge)
    except Exception:
        pass
