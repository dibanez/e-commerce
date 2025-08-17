"""
Template filters for cart functionality.
"""
from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument.
    Usage: {{ price|mul:quantity }}
    """
    try:
        # Handle None or empty values
        if value is None or arg is None:
            return 0
            
        # Convert to string and handle empty strings
        value_str = str(value).strip()
        arg_str = str(arg).strip()
        
        if not value_str or not arg_str:
            return 0
            
        return Decimal(value_str) * Decimal(arg_str)
    except (ValueError, TypeError, AttributeError, InvalidOperation):
        return 0


@register.filter
def currency(value):
    """
    Formats a value as currency.
    Usage: {{ price|currency }}
    """
    try:
        # Handle None or empty values
        if value is None:
            return "€0.00"
            
        # Convert to string and handle empty strings
        value_str = str(value).strip()
        
        if not value_str:
            return "€0.00"
            
        return f"€{Decimal(value_str):.2f}"
    except (ValueError, TypeError, AttributeError, InvalidOperation):
        return "€0.00"
