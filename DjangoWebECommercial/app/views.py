"""Django views for the storefront."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import AddToCartForm, CheckoutForm
from .models import AdminToken, AnonymousCart, CartItem, Category, Order, OrderItem, Product, ProductAttributeValue

DEFAULT_PAGE_SIZE = 18
MAX_PAGE_SIZE = 100


def build_category_path(category):
    path = []
    while category:
        path.append(category)
        category = category.parent
    return list(reversed(path))


def get_page_size(request):
    try:
        return max(1, min(int(request.GET.get('page_size', DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE))
    except (TypeError, ValueError):
        return DEFAULT_PAGE_SIZE


def get_filtered_products(request, category_slug=None):
    """Build the shared catalog/API product queryset and selected category."""
    products = Product.objects.select_related('category')
    category = None
    slug = category_slug or request.GET.get('category')
    if slug:
        category = get_object_or_404(Category, slug=slug)
        category_ids = [category.pk, *category.children.values_list('pk', flat=True)]
        products = products.filter(category_id__in=category_ids)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(name__icontains=query)
    for parameter, lookup in (('min_price', 'price__gte'), ('max_price', 'price__lte')):
        value = request.GET.get(parameter)
        if value:
            try:
                products = products.filter(**{lookup: Decimal(value)})
            except InvalidOperation:
                pass
    for key in request.GET:
        if not key.startswith('attr_'):
            continue
        try:
            attribute_id = int(key.removeprefix('attr_'))
        except ValueError:
            continue
        values = request.GET.getlist(key)
        if values:
            products = products.filter(attributes__attribute_id=attribute_id, attributes__value__in=values)
    ordering = {'price_asc': 'price', 'price_desc': '-price'}.get(request.GET.get('sort'), '-created_at')
    return products.order_by(ordering).distinct(), category


def get_attribute_facets(products):
    """Return all visible attribute/value counts in one aggregate query."""
    rows = ProductAttributeValue.objects.filter(product__in=products).values(
        'attribute_id', 'attribute__name', 'value'
    ).annotate(product_count=Count('product_id', distinct=True)).order_by('attribute__name', 'value')
    facets = {}
    for row in rows:
        facet = facets.setdefault(row['attribute_id'], {'id': row['attribute_id'], 'name': row['attribute__name'], 'values': []})
        facet['values'].append({'value': row['value'], 'count': row['product_count']})
    return list(facets.values())


def home(request):
    return render(request, 'app/index.html', {
        'title': 'Home', 'year': datetime.now().year,
        'top_products': Product.objects.filter(is_top=True).order_by('-created_at')[:8],
        'categories': Category.objects.filter(parent__isnull=True).prefetch_related('children'),
    })


def category_view(request, slug=None):
    products, category = get_filtered_products(request, slug)
    page = Paginator(products, get_page_size(request)).get_page(request.GET.get('page', 1))
    return render(request, 'app/category.html', {
        'categories': Category.objects.filter(parent__isnull=True).prefetch_related('children'),
        'category': category, 'products': page.object_list, 'attributes': get_attribute_facets(products),
        'breadcrumb': build_category_path(category) if category else [], 'page': page, 'page_size': page.paginator.per_page,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'app/product.html', {
        'product': product, 'add_form': AddToCartForm(initial={'product_id': product.pk}),
        'attributes': product.attributes.select_related('attribute'),
    })


def get_or_create_cart(request):
    token = request.COOKIES.get('cart_token')
    if token:
        return AnonymousCart.objects.get_or_create(token=token)[0], None
    cart = AnonymousCart.objects.create()
    return cart, cart.token


@require_POST
@transaction.atomic
def add_to_cart(request):
    form = AddToCartForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    product = get_object_or_404(Product, pk=form.cleaned_data['product_id'])
    cart, new_token = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': form.cleaned_data['quantity']})
    if not created:
        CartItem.objects.filter(pk=item.pk).update(quantity=F('quantity') + form.cleaned_data['quantity'])
    response = JsonResponse({'ok': True, 'cart_token': new_token})
    if new_token:
        response.set_cookie('cart_token', new_token, httponly=True, samesite='Lax')
    return response


def view_cart(request):
    token = request.COOKIES.get('cart_token')
    items = CartItem.objects.filter(cart__token=token).select_related('product') if token else CartItem.objects.none()
    return render(request, 'app/cart.html', {'items': items})


@transaction.atomic
def checkout(request):
    token = request.COOKIES.get('cart_token')
    if not token:
        return redirect('home')
    cart = get_object_or_404(AnonymousCart.objects.select_for_update(), token=token)
    items = list(cart.items.select_for_update().select_related('product'))
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            total = sum((item.product.price * item.quantity for item in items), Decimal('0'))
            order = Order.objects.create(token=cart.token, total=total, **form.cleaned_data)
            OrderItem.objects.bulk_create([OrderItem(order=order, product=item.product, quantity=item.quantity, price=item.product.price) for item in items])
            cart.items.all().delete()
            return render(request, 'app/checkout_success.html', {'order': order})
    else:
        form = CheckoutForm()
    return render(request, 'app/checkout.html', {'form': form, 'items': items})


@require_GET
def admin_api_products(request):
    token = request.META.get('HTTP_X_ADMIN_TOKEN')
    if not token:
        return HttpResponseForbidden('Missing admin token')
    if not AdminToken.objects.filter(token=token, is_active=True).exists():
        return HttpResponseForbidden('Invalid admin token')
    products = Product.objects.all()
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(name__icontains=query)
    return JsonResponse({'products': list(products.values('id', 'name', 'price', 'category__name'))})


@require_GET
def api_products(request):
    products, _ = get_filtered_products(request)
    page = Paginator(products, get_page_size(request)).get_page(request.GET.get('page', 1))
    return JsonResponse({'products': [
        {'id': product.pk, 'name': product.name, 'price': str(product.price), 'slug': product.slug,
         'image': product.image.url if product.image else None, 'category': product.category.name if product.category else None}
        for product in page.object_list
    ], 'has_next': page.has_next(), 'page': page.number})


def search_view(request):
    return category_view(request)


def contact(request):
    return render(request, 'app/contact.html', {'title': 'Contact', 'message': 'Your contact page.', 'year': datetime.now().year})


def about(request):
    return render(request, 'app/about.html', {'title': 'About', 'message': 'Your application description page.', 'year': datetime.now().year})

