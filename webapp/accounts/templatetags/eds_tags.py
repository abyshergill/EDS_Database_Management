from django import template

from accounts.decorators import is_app_admin

register = template.Library()

FIELD_LABELS = {
    "component": "Component",
    "vhx_remark": "VHX remark",
    "eds_remark": "EDS remark",
    "remark": "Remark",
    "vhx_image": "VHX image",
    "eds_image": "EDS image",
}


@register.filter
def is_admin(user):
    return is_app_admin(user)


@register.filter
def field_label(name):
    return FIELD_LABELS.get(name, name.replace("_", " ").capitalize())


@register.simple_tag(takes_context=True)
def query_with(context, **kwargs):
    """Rebuild the current querystring with some keys replaced (for pagination)."""
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()
