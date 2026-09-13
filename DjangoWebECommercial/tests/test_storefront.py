from decimal import Decimal

import pytest
from django.core.management import call_command
from django.urls import reverse

from app.models import (
    AnonymousCart,
    CartItem,
    Category,
    Order,
    Product,
    ProductAttribute,
    ProductAttributeValue,
)


@pytest.fixture
def catalog():
    root = Category.objects.create(name='Electronics')
    phones = Category.objects.create(name='Phones', parent=root)
    other = Category.objects.create(name='Books')
    red_phone = Product.objects.create(
        name='Red Phone', category=phones, price=Decimal('199.99'), is_top=True,
    )
    Product.objects.create(name='Blue Phone', category=phones, price=Decimal('299.99'))
    Product.objects.create(name='Python Book', category=other, price=Decimal('25.00'))
    color = ProductAttribute.objects.create(name='Color')
    ProductAttributeValue.objects.create(product=red_phone, attribute=color, value='Red')
    return {'root': root, 'phones': phones, 'product': red_phone, 'color': color}


@pytest.mark.django_db
def test_category_filters_products_and_exposes_facets(client, catalog):
    response = client.get(
        reverse('category', args=[catalog['root'].slug]),
        {
            'min_price': '100',
            f"attr_{catalog['color'].pk}": 'Red',
            'page': 'not-a-number',
            'page_size': '100000',
        },
    )

    assert response.status_code == 200
    assert list(response.context['products']) == [catalog['product']]
    assert response.context['page'].paginator.per_page == 100
    assert response.context['attributes'] == [{
        'id': catalog['color'].pk,
        'name': 'Color',
        'values': [{'value': 'Red', 'count': 1}],
    }]


@pytest.mark.django_db
def test_product_api_applies_category_filter_and_handles_invalid_pagination(client, catalog):
    response = client.get(
        reverse('api_products'),
        {'category': catalog['root'].slug, 'page': 'invalid', 'page_size': '-1'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['page'] == 1
    assert payload['has_next'] is True
    assert len(payload['products']) == 1


@pytest.mark.django_db
def test_add_to_cart_creates_cart_and_accumulates_quantity(client, catalog):
    url = reverse('add_to_cart')
    data = {'product_id': catalog['product'].pk, 'quantity': 2}

    first_response = client.post(url, data)
    second_response = client.post(url, {'product_id': catalog['product'].pk, 'quantity': 3})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    cart = AnonymousCart.objects.get(token=client.cookies['cart_token'].value)
    assert CartItem.objects.get(cart=cart, product=catalog['product']).quantity == 5


@pytest.mark.django_db
def test_checkout_creates_order_and_clears_cart(client, catalog):
    cart = AnonymousCart.objects.create()
    CartItem.objects.create(cart=cart, product=catalog['product'], quantity=2)
    client.cookies['cart_token'] = cart.token

    response = client.post(reverse('checkout'), {
        'full_name': 'Test Buyer',
        'email': 'buyer@example.com',
        'address': '1 Test Street',
    })

    assert response.status_code == 200
    order = Order.objects.get()
    assert order.total == Decimal('399.98')
    assert order.items.get().quantity == 2
    assert not CartItem.objects.filter(cart=cart).exists()


@pytest.mark.django_db
def test_product_api_is_get_only(client, catalog):
    assert client.post(reverse('api_products')).status_code == 405


@pytest.mark.django_db
def test_menu_ajax_returns_only_direct_subcategories(client, catalog):
    response = client.get(reverse('ajax_subcategories', args=[catalog['root'].slug]))

    assert response.status_code == 200
    assert response.json() == {
        'children': [{'name': 'Phones', 'slug': catalog['phones'].slug}],
    }


@pytest.mark.django_db
def test_about_contact_and_footer_describe_current_project(client, catalog):
    about = client.get(reverse('about'))
    contact = client.get(reverse('contact'))

    assert about.status_code == 200
    assert 'vanilla Django' in about.content.decode()
    assert contact.status_code == 200
    assert 'github.com/Yaroslav-Repos/DjangoWebECommercial' in contact.content.decode()
    assert reverse('about') in about.content.decode()
    assert reverse('contact') in about.content.decode()


@pytest.mark.django_db
def test_seed_data_creates_an_idempotent_mock_catalog():
    call_command('seed_data')
    call_command('seed_data')

    assert Category.objects.count() == 12
    assert Product.objects.count() == 64
    assert Product.objects.filter(is_top=True).count() == 16
    assert ProductAttributeValue.objects.count() == 192
