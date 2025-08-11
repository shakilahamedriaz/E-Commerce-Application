"""
Carbon intelligence service for smart environmental insights and gamification
"""
from decimal import Decimal
from django.db.models import Avg
from ..models import Product, EnvironmentalImpact, Badge, UserImpact, UserBadge


def analyze_product_carbon_impact(product):
    """Analyze if product qualifies for low-carbon badge popup"""
    
    # Get category average carbon footprint
    category_avg = Product.objects.filter(
        category=product.category,
        carbon_footprint_kg__isnull=False
    ).aggregate(avg_carbon=Avg('carbon_footprint_kg'))['avg_carbon'] or Decimal('0')
    
    product_carbon = product.effective_carbon_kg()
    
    # Calculate reduction percentage
    if category_avg > 0:
        reduction_percent = ((category_avg - product_carbon) / category_avg) * 100
    else:
        reduction_percent = 0
    
    # Determine badge eligibility
    badge_eligible = False
    badge_type = None
    popup_message = ""
    badge_icon = "🌱"
    
    if reduction_percent >= 30:
        badge_eligible = True
        badge_type = "ECO_CHAMPION"
        badge_icon = "🌟"
        popup_message = f"Amazing choice! This product has {reduction_percent:.0f}% lower carbon footprint than average in its category!"
    elif reduction_percent >= 20:
        badge_eligible = True
        badge_type = "GREEN_CHOICE"
        badge_icon = "🌿"
        popup_message = f"Great green choice! {reduction_percent:.0f}% lower carbon footprint than category average!"
    elif reduction_percent >= 10:
        badge_eligible = True
        badge_type = "ECO_FRIENDLY"
        badge_icon = "🍃"
        popup_message = f"Nice eco-friendly option with {reduction_percent:.0f}% less carbon than average!"
    
    return {
        'badge_eligible': badge_eligible,
        'badge_type': badge_type,
        'badge_icon': badge_icon,
        'popup_message': popup_message,
        'reduction_percent': reduction_percent,
        'category_avg': category_avg,
        'product_carbon': product_carbon,
        'potential_saving': max(category_avg - product_carbon, Decimal('0'))
    }


def get_environmental_equivalents(carbon_saved_kg):
    """Convert carbon savings to environmental equivalents"""
    equivalents = []
    
    # Hardcoded environmental metrics (we'll create these in database later)
    metrics_data = [
        {
            'metric_name': 'Trees Planted',
            'co2_per_unit': Decimal('21.77'),  # kg CO2 absorbed per tree per year
            'unit_label': 'trees',
            'description': 'Number of trees that would absorb this much CO₂ in a year',
            'icon': '🌳'
        },
        {
            'metric_name': 'Car Miles Avoided',
            'co2_per_unit': Decimal('0.404'),  # kg CO2 per mile (average car)
            'unit_label': 'miles',
            'description': 'Miles of car driving that would produce this much CO₂',
            'icon': '🚗'
        },
        {
            'metric_name': 'LED Lightbulb Hours',
            'co2_per_unit': Decimal('0.00004'),  # kg CO2 per hour (LED bulb)
            'unit_label': 'hours',
            'description': 'Hours of LED lightbulb usage equivalent',
            'icon': '💡'
        },
        {
            'metric_name': 'Smartphone Charges',
            'co2_per_unit': Decimal('0.00841'),  # kg CO2 per charge
            'unit_label': 'charges',
            'description': 'Smartphone charges equivalent in carbon footprint',
            'icon': '📱'
        },
        {
            'metric_name': 'Plant-based Meals',
            'co2_per_unit': Decimal('2.0'),  # kg CO2 per plant meal vs meat meal saved
            'unit_label': 'meals',
            'description': 'Plant-based meals chosen instead of meat meals',
            'icon': '🥗'
        }
    ]
    
    for metric in metrics_data:
        if carbon_saved_kg > 0:
            equivalent_value = carbon_saved_kg / metric['co2_per_unit']
            if equivalent_value >= 0.1:  # Only show if meaningful
                equivalents.append({
                    'metric': metric['metric_name'],
                    'value': round(float(equivalent_value), 1),
                    'unit': metric['unit_label'],
                    'description': metric['description'],
                    'icon': metric['icon']
                })
    
    return equivalents


def generate_impact_story(user):
    """Generate personalized environmental impact story"""
    try:
        impact = UserImpact.objects.get(user=user)
        total_saved = impact.total_saved_kg
    except UserImpact.DoesNotExist:
        total_saved = Decimal('0')
    
    if total_saved <= 0:
        return {
            'story': "🌱 Start your environmental journey today!",
            'equivalents': [],
            'next_milestone': 5.0,
            'progress_to_next': 0,
            'total_saved': total_saved
        }
    
    equivalents = get_environmental_equivalents(total_saved)
    
    # Generate story based on savings
    if total_saved >= 100:
        story = f"🏆 Amazing! You've saved {total_saved}kg of CO₂ - that's like a climate superhero!"
    elif total_saved >= 50:
        story = f"🌟 Fantastic! Your {total_saved}kg CO₂ savings are making a real difference!"
    elif total_saved >= 20:
        story = f"🌿 Great progress! You've saved {total_saved}kg of CO₂ for our planet!"
    elif total_saved >= 5:
        story = f"🌱 Well done! Your {total_saved}kg CO₂ savings are growing!"
    else:
        story = f"🌱 Good start! Every gram counts - you've saved {total_saved}kg CO₂!"
    
    # Calculate next milestone
    milestones = [5, 10, 20, 50, 100, 200, 500]
    next_milestone = next((m for m in milestones if m > total_saved), 1000)
    
    return {
        'story': story,
        'equivalents': equivalents,
        'total_saved': total_saved,
        'next_milestone': next_milestone,
        'progress_to_next': min((float(total_saved) / next_milestone) * 100, 100)
    }


def award_carbon_badge(user, badge_type, order=None):
    """Award carbon reduction badge to user"""
    try:
        badge = Badge.objects.get(code=badge_type)
        user_badge, created = UserBadge.objects.get_or_create(
            user=user,
            badge=badge
        )
        
        if created:
            # Create notification about new badge
            from .notifications import create_notification
            create_notification(
                user=user,
                title=f"🏆 New Badge Earned: {badge.name}",
                message=f"Congratulations! You've earned the '{badge.name}' badge for your eco-friendly choices!",
                notification_type='sustainability'
            )
            return True
    except Badge.DoesNotExist:
        pass
    
    return False


def check_carbon_achievements(user, order):
    """Check if user qualifies for any carbon-related achievements"""
    try:
        impact = UserImpact.objects.get(user=user)
        total_saved = impact.total_saved_kg
        
        # Tree planter achievement (equivalent to 1 tree = 21.77kg CO2/year)
        trees_equivalent = total_saved / Decimal('21.77')
        if trees_equivalent >= 1:
            award_carbon_badge(user, 'TREE_PLANTER')
        
        # Milestone achievements
        if total_saved >= 100:
            award_carbon_badge(user, 'CARBON_HERO')
        elif total_saved >= 50:
            award_carbon_badge(user, 'ECO_WARRIOR')
        elif total_saved >= 20:
            award_carbon_badge(user, 'GREEN_GUARDIAN')
        
    except UserImpact.DoesNotExist:
        pass


def calculate_global_impact_context(carbon_saved_kg):
    """Calculate global context for user's carbon savings"""
    if carbon_saved_kg <= 0:
        return {}
    
    # Global context calculations (approximate values)
    world_daily_emissions = 100_000_000_000  # kg CO2 daily (100 billion kg)
    avg_household_annual = 16000  # kg CO2 per year
    
    return {
        'world_percentage': (float(carbon_saved_kg) / world_daily_emissions) * 100,
        'households_equivalent': float(carbon_saved_kg) / avg_household_annual,
        'days_of_breathing': float(carbon_saved_kg) / 0.9,  # Avg human CO2 per day
        'gasoline_gallons': float(carbon_saved_kg) / 8.89,  # kg CO2 per gallon
    }


def simulate_future_impact(carbon_reduction_monthly, timeframe_months):
    """Simulate future environmental impact"""
    total_savings = carbon_reduction_monthly * timeframe_months
    annual_savings = carbon_reduction_monthly * 12
    
    equivalents = get_environmental_equivalents(annual_savings)
    global_context = calculate_global_impact_context(annual_savings)
    
    return {
        'total_savings': total_savings,
        'annual_savings': annual_savings,
        'equivalents': equivalents,
        'global_context': global_context,
        'monthly_reduction': carbon_reduction_monthly,
        'timeframe': timeframe_months
    }
