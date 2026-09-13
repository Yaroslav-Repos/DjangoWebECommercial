"""Create an idempotent mock catalog for local development."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from app.models import Category, Product, ProductAttribute, ProductAttributeValue


CATALOG = (
    ('electronics', 'Electronics', (
        ('smartphones', 'Smartphones', 'Phone', ('Apple', 'Samsung', 'Google', 'Xiaomi'), Decimal('299.00')),
        ('audio', 'Audio', 'Headphones', ('Sony', 'JBL', 'Bose', 'Anker'), Decimal('59.00')),
    )),
    ('computers', 'Computers', (
        ('laptops', 'Laptops', 'Laptop', ('Lenovo', 'Dell', 'Asus', 'Acer'), Decimal('549.00')),
        ('monitors', 'Monitors', 'Monitor', ('LG', 'Samsung', 'Dell', 'AOC'), Decimal('179.00')),
    )),
    ('home', 'Home and Kitchen', (
        ('coffee-machines', 'Coffee Machines', 'Coffee Machine', ('Philips', 'DeLonghi', 'Bosch', 'Krups'), Decimal('129.00')),
        ('vacuum-cleaners', 'Vacuum Cleaners', 'Vacuum Cleaner', ('Xiaomi', 'Dyson', 'Bosch', 'Rowenta'), Decimal('99.00')),
    )),
    ('sports', 'Sports and Outdoors', (
        ('bicycles', 'Bicycles', 'Bicycle', ('Trek', 'Giant', 'Merida', 'Scott'), Decimal('399.00')),
        ('fitness', 'Fitness', 'Fitness Tracker', ('Garmin', 'Xiaomi', 'Huawei', 'Fitbit'), Decimal('49.00')),
    )),
)

COLORS = ('Black', 'White', 'Blue', 'Silver')
WARRANTIES = ('12 months', '24 months')


class Command(BaseCommand):
    help = 'Create an idempotent mock catalog with 64 products for local development.'

    def handle(self, *args, **options):
        brand_attribute, _ = ProductAttribute.objects.get_or_create(name='Brand')
        color_attribute, _ = ProductAttribute.objects.get_or_create(name='Color')
        warranty_attribute, _ = ProductAttribute.objects.get_or_create(name='Warranty')

        created_products = 0
        existing_products = 0

        for parent_slug, parent_name, subcategories in CATALOG:
            parent, _ = Category.objects.get_or_create(
                slug=parent_slug,
                defaults={'name': parent_name},
            )

            for category_slug, category_name, product_type, brands, base_price in subcategories:
                category, _ = Category.objects.get_or_create(
                    slug=category_slug,
                    defaults={'name': category_name, 'parent': parent},
                )

                for number in range(1, 9):
                    brand = brands[(number - 1) % len(brands)]
                    color = COLORS[(number - 1) % len(COLORS)]
                    warranty = WARRANTIES[number % len(WARRANTIES)]
                    slug = f'{category_slug}-{brand.lower()}-{number}'
                    product, created = Product.objects.get_or_create(
                        slug=slug,
                        defaults={
                            'name': f'{brand} {product_type} {number}',
                            'category': category,
                            'description': f'Mock {product_type.lower()} for local development and UI testing.',
                            'price': base_price + (Decimal(number) * Decimal('25.00')),
                            'is_top': number <= 2,
                        },
                    )

                    if created:
                        created_products += 1
                    else:
                        existing_products += 1

                    for attribute, value in (
                        (brand_attribute, brand),
                        (color_attribute, color),
                        (warranty_attribute, warranty),
                    ):
                        ProductAttributeValue.objects.get_or_create(
                            product=product,
                            attribute=attribute,
                            value=value,
                        )

        self.stdout.write(self.style.SUCCESS(
            f'Mock catalog ready: {created_products} products created, '
            f'{existing_products} products already existed.'
        ))
