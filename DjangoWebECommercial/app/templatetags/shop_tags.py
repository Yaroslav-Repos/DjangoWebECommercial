from django import template
from app.models import Category
register = template.Library()

@register.filter
def get_breadcrumb(category):
    path = []
    cat = category
    while cat:
        path.insert(0, cat)
        cat = cat.parent
    return path

@register.filter
def product_breadcrumb(product):

    result = []
    if product and product.category:
        for c in get_breadcrumb(product.category):
            result.append({'type': 'category', 'obj': c})
    if product:
        result.append({'type': 'product', 'obj': product})
    return result


@register.filter
def getlist(qdict_or_request, key):

    try:

        if hasattr(qdict_or_request, 'GET'):

            return qdict_or_request.GET.getlist(key)
        else:

            return qdict_or_request.getlist(key)
    except Exception:

        try:
            if hasattr(qdict_or_request, 'GET'):
                v = qdict_or_request.GET.get(key)
            else:
                v = qdict_or_request.get(key)
            return [v] if v else []
        except Exception:
            return []


@register.filter
def dict_get(d, key):
    try:
        return d.get(key, 0)
    except Exception:
        return 0


@register.filter
def is_attr_checked(value, attr_data):

    try:
        if not attr_data or '|' not in str(attr_data):
            return False
        parts = str(attr_data).split('|')
        if len(parts) < 2:
            return False

        return False
    except Exception:
        return False
