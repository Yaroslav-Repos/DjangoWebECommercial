from django.contrib import admin
from .models import Category, Product, ProductAttribute, ProductAttributeValue, AnonymousCart, CartItem, Order, OrderItem, AdminToken


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_top', 'image_tag')
    list_filter = ('category', 'is_top')
    search_fields = ('name',)
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return f"<img src='/{obj.image.url}' style='max-height:50px;' />"
        return ''
    image_tag.allow_tags = True
    image_tag.short_description = 'Image'


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'value')
    search_fields = ('product__name', 'attribute__name', 'value')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'total', 'status', 'created_at')
    search_fields = ('full_name', 'email')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')


@admin.register(AdminToken)
class AdminTokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'token', 'is_active', 'created_by', 'created_at')
    search_fields = ('name', 'token')
# end of admin definitions
