from django.core.management.base import BaseCommand
from shop.models import Badge, EnvironmentalImpact
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed environmental data including badges and metrics'

    def handle(self, *args, **options):
        self.stdout.write('Seeding environmental data...')
        
        # Create environmental badges
        badges_data = [
            {
                'code': 'ECO_FRIENDLY',
                'name': 'Eco Friendly',
                'description': 'Awarded for choosing products with 10%+ lower carbon footprint',
                'category': 'carbon_reduction',
                'icon': '🍃',
                'popup_message': 'Great choice! This product has a lower environmental impact.'
            },
            {
                'code': 'GREEN_CHOICE',
                'name': 'Green Choice',
                'description': 'Awarded for choosing products with 20%+ lower carbon footprint',
                'category': 'carbon_reduction',
                'icon': '🌿',
                'popup_message': 'Excellent green choice with significantly lower carbon footprint!'
            },
            {
                'code': 'ECO_CHAMPION',
                'name': 'Eco Champion',
                'description': 'Awarded for choosing products with 30%+ lower carbon footprint',
                'category': 'carbon_reduction',
                'icon': '🌟',
                'popup_message': 'Outstanding! You\'re an environmental champion!'
            },
            {
                'code': 'TREE_PLANTER',
                'name': 'Tree Planter',
                'description': 'Saved equivalent CO₂ absorption of 1 tree per year',
                'category': 'milestone',
                'icon': '🌳',
                'popup_message': 'Your savings equal planting a tree!'
            },
            {
                'code': 'GREEN_GUARDIAN',
                'name': 'Green Guardian',
                'description': 'Saved 20kg+ of CO₂ through eco-friendly purchases',
                'category': 'milestone',
                'icon': '🛡️',
                'popup_message': 'You\'re protecting our planet!'
            },
            {
                'code': 'ECO_WARRIOR',
                'name': 'Eco Warrior',
                'description': 'Saved 50kg+ of CO₂ through sustainable choices',
                'category': 'milestone',
                'icon': '⚔️',
                'popup_message': 'Fighting climate change one purchase at a time!'
            },
            {
                'code': 'CARBON_HERO',
                'name': 'Carbon Hero',
                'description': 'Saved 100kg+ of CO₂ - truly making a difference!',
                'category': 'milestone',
                'icon': '🦸',
                'popup_message': 'You\'re a true environmental hero!'
            }
        ]
        
        created_badges = 0
        for badge_data in badges_data:
            badge, created = Badge.objects.get_or_create(
                code=badge_data['code'],
                defaults=badge_data
            )
            if created:
                created_badges += 1
                self.stdout.write(f'Created badge: {badge.name}')
        
        self.stdout.write(f'Created {created_badges} new badges')
        
        # Create environmental impact metrics
        metrics_data = [
            {
                'metric_name': 'Trees Planted',
                'co2_per_unit': Decimal('21.77'),
                'unit_label': 'trees',
                'description': 'Number of trees that would absorb this much CO₂ in a year',
                'icon': '🌳'
            },
            {
                'metric_name': 'Car Miles Avoided',
                'co2_per_unit': Decimal('0.404'),
                'unit_label': 'miles',
                'description': 'Miles of car driving that would produce this much CO₂',
                'icon': '🚗'
            },
            {
                'metric_name': 'LED Lightbulb Hours',
                'co2_per_unit': Decimal('0.00004'),
                'unit_label': 'hours',
                'description': 'Hours of LED lightbulb usage equivalent',
                'icon': '💡'
            },
            {
                'metric_name': 'Smartphone Charges',
                'co2_per_unit': Decimal('0.00841'),
                'unit_label': 'charges',
                'description': 'Smartphone charges equivalent in carbon footprint',
                'icon': '📱'
            },
            {
                'metric_name': 'Plant-based Meals',
                'co2_per_unit': Decimal('2.0'),
                'unit_label': 'meals',
                'description': 'Plant-based meals chosen instead of meat meals',
                'icon': '🥗'
            },
            {
                'metric_name': 'Plastic Bottles Recycled',
                'co2_per_unit': Decimal('0.082'),
                'unit_label': 'bottles',
                'description': 'Plastic bottles recycled instead of thrown away',
                'icon': '♻️'
            },
            {
                'metric_name': 'Energy-Efficient Appliances',
                'co2_per_unit': Decimal('365.0'),
                'unit_label': 'appliances',
                'description': 'Annual CO₂ savings from energy-efficient appliances',
                'icon': '⚡'
            }
        ]
        
        created_metrics = 0
        for metric_data in metrics_data:
            metric, created = EnvironmentalImpact.objects.get_or_create(
                metric_name=metric_data['metric_name'],
                defaults=metric_data
            )
            if created:
                created_metrics += 1
                self.stdout.write(f'Created metric: {metric.metric_name}')
        
        self.stdout.write(f'Created {created_metrics} new environmental metrics')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded environmental data:\n'
                f'- {created_badges} badges\n'
                f'- {created_metrics} environmental metrics'
            )
        )
