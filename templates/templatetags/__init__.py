from django import template

register = template.Library()

@register.filter
def filter_active(users):
    return [user for user in users if user.is_active]

@register.filter
def filter_inactive(users):
    return [user for user in users if not user.is_active]

@register.filter
def filter_active_drivers(drivers):
    return [driver for driver in drivers if driver.user.is_active]

@register.filter
def multiply(value, arg):
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0