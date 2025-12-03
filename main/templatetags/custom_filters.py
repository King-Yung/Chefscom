from django import template

register = template.Library()

@register.filter
def add_space_after_comma(value):
    if value:
        return value.replace(",", ", ")
    return ""
