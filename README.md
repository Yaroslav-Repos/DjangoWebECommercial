# Django Web E-Commerce

A small server-rendered e-commerce storefront built with vanilla Django. It includes a category catalog, product attributes and filters, anonymous shopping carts, checkout/order creation, Django admin, JSON catalog endpoints, and a pytest-django test suite.

## Features

- Nested product categories with a catalog drawer
- Product listing with search, price range, attribute filters, sorting, and pagination
- Product detail pages with images and attributes
- Cookie-backed anonymous carts
- Atomic checkout that creates orders and order items
- Django admin for catalog, orders, and API tokens
- JSON endpoints for product lists and category previews
- Sample catalog data command
- Automated pytest-django coverage for core storefront behavior

## Tech stack

- Python
- Django
- SQLite (default development database)
- Bootstrap and jQuery for the existing storefront UI
- pytest and pytest-django

## Quick start

Prerequisites: Python 3.10+ and pip.

```bash
git clone https://github.com/Yaroslav-Repos/DjangoWebECommercial
cd DjangoWebECommercial

python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install dependencies and prepare the database:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

## Sample data

The included seed command creates categories, products, and product attributes. It optionally downloads placeholder images, so install `requests` before running it:

```bash
pip install requests
python manage.py seed_data
```

## Admin

Create an administrator account:

```bash
python manage.py createsuperuser
```

Then sign in at <http://127.0.0.1:8000/admin/> to manage categories, products, product attributes, orders etc.

## Tests

The test suite uses pytest-django and an isolated test database:

```bash
pytest
```

It covers catalog filtering and facets, API pagination, carts, checkout, access control for the admin API, and category-preview AJAX responses.

## Routes

| Route | Purpose |
| --- | --- |
| `/` | Home page and top products |
| `/category/` | Full product catalog |
| `/category/<slug>/` | Category product catalog |
| `/product/<slug>/` | Product details |
| `/cart/` | Anonymous cart |
| `/checkout/` | Checkout |
| `/search/?q=<query>` | Product search |
| `/api/products/` | Filtered product JSON API |
| `/api/admin/products/` | Token-protected product JSON API |
| `/ajax/subcategories/<slug>/` | Category navigation/preview JSON |

## Product API

`GET /api/products/` accepts these optional query parameters:

| Parameter | Example | Description |
| --- | --- | --- |
| `category` | `electronics` | Category slug |
| `q` | `phone` | Product-name search |
| `min_price` | `100` | Minimum price |
| `max_price` | `500` | Maximum price |
| `sort` | `price_asc` | `price_asc`, `price_desc`, or newest by default |
| `attr_<id>` | `attr_1=Black` | Product attribute value; may be repeated |
| `page` | `2` | Page number |
| `page_size` | `18` | Results per page (limited to 100) |

The admin endpoint requires an active token in the `X-Admin-Token` request header.

## Project layout

```text
app/
  management/commands/seed_data.py  # Sample catalog command
  templates/app/                    # Django templates
  views.py                          # Storefront, API, cart, and checkout views
  models.py                         # Catalog, cart, order, and token models
DjangoWebECommercial/
  settings.py                       # Project configuration
  urls.py                           # URL routes
tests/
  test_storefront.py                # pytest-django tests
```

## Development notes

This repository is configured for development: `DEBUG=True`, a local SQLite database, and development-only media serving. Before deploying, move `SECRET_KEY` and configuration into environment variables, set `DEBUG=False`, configure `ALLOWED_HOSTS`, use a production database, and serve static/media files through appropriate production infrastructure.
