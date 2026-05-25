from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Category, Product


def ajax_subcategories(request, slug):

    cat = get_object_or_404(Category, slug=slug)
    children = []
    for ch in cat.children.all():
        children.append({'id': ch.id, 'name': ch.name, 'slug': ch.slug})


    prods = Product.objects.filter(category=cat)[:4]
    products = []
    for p in prods:
        products.append({'id': p.id, 'name': p.name, 'slug': p.slug, 'image': p.image.url if p.image else None, 'price': str(p.price)})

    return JsonResponse({'id': cat.id, 'name': cat.name, 'children': children, 'products': products})
