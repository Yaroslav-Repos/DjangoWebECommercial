from django.core.management.base import BaseCommand
from app.models import Category, Product, ProductAttribute, ProductAttributeValue
from django.core.files.base import ContentFile
import requests

class Command(BaseCommand):
    help = 'Seed sample categories and products'

    def handle(self, *args, **options):
        # create categories (idempotent)
        c_elect, _ = Category.objects.get_or_create(name='Електроніка', slug='electronics')
        c_phone, _ = Category.objects.get_or_create(name='Телефони', slug='phones', parent=c_elect)
        c_lap, _ = Category.objects.get_or_create(name='Ноутбуки', slug='laptops', parent=c_elect)

        # attributes (idempotent)
        attr_brand, _ = ProductAttribute.objects.get_or_create(name='Бренд')
        attr_color, _ = ProductAttribute.objects.get_or_create(name='Колір')

        # sample products with placeholder images (idempotent by slug)
        # create multiple sample products for testing
        sample_products = [
            ('phone-model-a', 'Phone Model A', c_phone, 'Sample phone A', 199.99),
            ('phone-model-b', 'Phone Model B', c_phone, 'Sample phone B', 299.99),
            ('phone-model-c', 'Phone Model C', c_phone, 'Sample phone C', 399.99),
            ('laptop-model-a', 'Laptop Model A', c_lap, 'Sample laptop A', 699.99),
            ('laptop-model-b', 'Laptop Model B', c_lap, 'Sample laptop B', 799.99),
            ('laptop-model-c', 'Laptop Model C', c_lap, 'Sample laptop C', 999.99),
        ]
        created_items = []
        for slug, name, cat, desc, price in sample_products:
            p, created = Product.objects.get_or_create(slug=slug, defaults={'name': name, 'category': cat, 'description': desc, 'price': price})
            created_items.append((p, created))

        # fetch placeholder images and attach if product was just created or has no image
        try:
            r = requests.get('https://placehold.co/300')
            if r.status_code == 200:
                content = ContentFile(r.content)
                for p, created in created_items:
                    if created or not p.image:
                        p.image.save(f'{p.slug}.png', content, save=True)
        except Exception:
            self.stdout.write('Could not download placeholder images; skipping images.')

        # attribute values (idempotent)
        if created_items:
            p1, _ = created_items[0]
            ProductAttributeValue.objects.get_or_create(product=p1, attribute=attr_brand, value='BrandA')
            ProductAttributeValue.objects.get_or_create(product=p1, attribute=attr_color, value='Black')

            if len(created_items) > 1:
                p2, _ = created_items[1]
                ProductAttributeValue.objects.get_or_create(product=p2, attribute=attr_brand, value='BrandB')
                ProductAttributeValue.objects.get_or_create(product=p2, attribute=attr_color, value='Gray')

        self.stdout.write(self.style.SUCCESS('Seed data created or already present.'))
