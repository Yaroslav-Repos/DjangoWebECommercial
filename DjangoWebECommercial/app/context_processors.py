from .models import Category, Product


def site_categories(request):
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    top_products = Product.objects.filter(is_top=True).order_by('-created_at')[:8]
    return {'site_categories': categories, 'site_top_products': top_products}
