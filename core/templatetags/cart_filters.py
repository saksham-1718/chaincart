from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    # Remove currency symbols and commas
    value = str(value).replace('₹', '').replace(',', '').strip()
    try:
        result = int(value) * int(arg)  # or float(value) if you have decimals
    except ValueError:
        result = 0
    return result
