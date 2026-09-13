"""
Definition of urls for DjangoWebECommercial.
"""

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from app import views


urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('admin/', admin.site.urls),
    path('category/', views.category_view, name='category_root'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('product/<slug:slug>/', views.product_detail, name='product'),
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('api/products/', views.api_products, name='api_products'),
    path('ajax/subcategories/<slug:slug>/', views.ajax_subcategories, name='ajax_subcategories'),
    path('search/', views.search_view, name='search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
