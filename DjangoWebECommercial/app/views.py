"""
Definition of views.
"""

from datetime import datetime
from django.shortcuts import render
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from .models import Category, Product, ProductAttribute, ProductAttributeValue, AnonymousCart, CartItem, Order, OrderItem, AdminToken
from .forms import AddToCartForm, CheckoutForm
from django.views.decorators.http import require_POST
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from urllib.parse import urlencode
from django.db.models import Q
import json

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
        }
    )


def build_category_path(cat):
    path = []
    while cat:
        path.insert(0, cat)
        cat = cat.parent
    return path


def home(request):

    top_products = Product.objects.filter(is_top=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    return render(request, 'app/index.html', {'title': 'Home', 'year': datetime.now().year, 'top_products': top_products, 'categories': categories})


def category_view(request, slug=None):
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    category = None
    products = Product.objects.all().select_related('category')
    breadcrumb = []
    if slug:
        category = get_object_or_404(Category, slug=slug)

        descendant_ids = [category.id] + list(category.children.values_list('id', flat=True))
        products = products.filter(category__id__in=descendant_ids)
        breadcrumb = build_category_path(category)


    q = request.GET.get('q')
    if q:
        products = products.filter(name__icontains=q)


    try:
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            products = products.filter(price__gte=float(min_price))
        if max_price:
            products = products.filter(price__lte=float(max_price))
    except ValueError:
        pass


    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    else:

        products = products.order_by('-created_at')


    base_products = products


    attr_filters = {}
    for key in request.GET.keys():
        if key.startswith('attr_'):
            values = request.GET.getlist(key)
            if not values:
                continue
            try:
                attr_id = int(key.split('_', 1)[1])
                attr_filters[attr_id] = values
            except (ValueError, IndexError):
                pass


    for attr_id, values in attr_filters.items():

        q_filter = Q()
        for value in values:
            q_filter |= Q(attributes__attribute_id=attr_id, attributes__value=value)
        products = products.filter(q_filter).distinct()


    raw_attributes = ProductAttribute.objects.filter(productattributevalue__product__in=base_products).distinct()
    attributes = []
    for attr in raw_attributes:
        vals = list(ProductAttributeValue.objects.filter(attribute=attr, product__in=base_products).values_list('value', flat=True).distinct())

        counts = {}
        for v in vals:
            counts[v] = base_products.filter(attributes__attribute=attr, attributes__value=v).distinct().count()
        attributes.append({'attr': attr, 'values': vals, 'counts': counts})


    products = products.distinct()


    page = int(request.GET.get('page', '1'))
    page_size = int(request.GET.get('page_size', '18'))
    paginator = Paginator(products, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'categories': categories,
        'category': category,
        'products': page_obj.object_list,
        'attributes': attributes,
        'breadcrumb': breadcrumb,
        'page': page_obj,
        'page_size': page_size,
    }
    return render(request, 'app/category.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    add_form = AddToCartForm(initial={'product_id': product.id})

    attributes = product.attributes.select_related('attribute').all()
    return render(request, 'app/product.html', {'product': product, 'add_form': add_form, 'attributes': attributes})


def get_or_create_cart(request):
    token = request.COOKIES.get('cart_token')
    if token:
        cart, _ = AnonymousCart.objects.get_or_create(token=token)
        return cart, None
    cart = AnonymousCart.objects.create()
    return cart, cart.token


@require_POST
def add_to_cart(request):
    form = AddToCartForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    product = get_object_or_404(Product, id=form.cleaned_data['product_id'])
    quantity = form.cleaned_data['quantity']
    cart, new_token = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity
        item.save()
    res = JsonResponse({'ok': True, 'cart_token': new_token})
    if new_token:
        res.set_cookie('cart_token', new_token, httponly=True)
    return res


def view_cart(request):
    cart = None
    token = request.COOKIES.get('cart_token')
    items = []
    if token:
        try:
            cart = AnonymousCart.objects.get(token=token)
            items = cart.items.select_related('product')
        except AnonymousCart.DoesNotExist:
            items = []
    return render(request, 'app/cart.html', {'items': items})


@transaction.atomic
def checkout(request):
    token = request.COOKIES.get('cart_token')
    if not token:
        return redirect('home')
    cart = get_object_or_404(AnonymousCart, token=token)
    items = cart.items.select_related('product')
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            total = sum([it.product.price * it.quantity for it in items])
            order = Order.objects.create(
                token=cart.token,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data['address'],
                total=total,
            )
            for it in items:
                OrderItem.objects.create(order=order, product=it.product, quantity=it.quantity, price=it.product.price)

            cart.items.all().delete()
            return render(request, 'app/checkout_success.html', {'order': order})
    else:
        form = CheckoutForm()
    return render(request, 'app/checkout.html', {'form': form, 'items': items})


def admin_api_products(request):

    token = request.META.get('HTTP_X_ADMIN_TOKEN')
    if not token:
        return HttpResponseForbidden('Missing admin token')
    try:
        adm = AdminToken.objects.get(token=token, is_active=True)
    except AdminToken.DoesNotExist:
        return HttpResponseForbidden('Invalid admin token')


    if request.method == 'GET':
        q = request.GET.get('q')
        qs = Product.objects.all()
        if q:
            qs = qs.filter(name__icontains=q)
        data = list(qs.values('id', 'name', 'price', 'category__name'))
        return JsonResponse({'products': data})

    return JsonResponse({'ok': True})


def api_products(request):

    print(f"GET params: {dict(request.GET)}")

    qs = Product.objects.all().select_related('category')


    slug = request.GET.get('category')
    if slug:
        try:
            cat = Category.objects.get(slug=slug)
            descendant_ids = [cat.id] + list(cat.children.values_list('id', flat=True))
            qs = qs.filter(category__id__in=descendant_ids)
        except Category.DoesNotExist:
            pass


    q = request.GET.get('q')
    if q:
        qs = qs.filter(name__icontains=q)


    try:
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            qs = qs.filter(price__gte=float(min_price))
        if max_price:
            qs = qs.filter(price__lte=float(max_price))
    except ValueError:
        pass


    sort = request.GET.get('sort')
    if sort == 'price_asc':
        qs = qs.order_by('price')
    elif sort == 'price_desc':
        qs = qs.order_by('-price')
    else:

        qs = qs.order_by('-created_at')


    attr_filters = {}
    for key in request.GET.keys():
        if key.startswith('attr_'):
            values = request.GET.getlist(key)
            if not values:
                continue
            try:
                attr_id = int(key.split('_', 1)[1])
                attr_filters[attr_id] = values
            except (ValueError, IndexError):
                pass


    for attr_id, values in attr_filters.items():
        q_filter = Q()
        for value in values:
            q_filter |= Q(attributes__attribute_id=attr_id, attributes__value=value)
        qs = qs.filter(q_filter).distinct()

    qs = qs.distinct()
    print(f"Final products count: {qs.count()}")

    page = int(request.GET.get('page', '1'))
    page_size = int(request.GET.get('page_size', '18'))
    paginator = Paginator(qs, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'products': [], 'has_next': False})

    products = []
    for p in page_obj.object_list:
        products.append({
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
            'slug': p.slug,
            'image': p.image.url if p.image else None,
            'category': p.category.name if p.category else None,
        })

    print(f"Returning {len(products)} products")
    response_data = {'products': products, 'has_next': page_obj.has_next(), 'page': page}
    return JsonResponse(response_data)


def search_view(request):
   
    return category_view(request, slug=None)

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }
    )
