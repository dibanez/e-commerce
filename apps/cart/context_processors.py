"""
Context processors for cart app.
"""
from .services import CartService


def cart(request):
    """
    Add cart information to template context.
    """
    cart_service = CartService(
        user=request.user if hasattr(request, 'user') else None,
        session=request.session if hasattr(request, 'session') else None
    )
    
    try:
        cart_summary = cart_service.get_cart_summary()
        return {
            'cart': cart_summary,
            'cart_total_items': cart_summary['total_items'],
            'cart_subtotal': cart_summary['subtotal'],
        }
    except Exception:
        # Return empty cart data if there's any error
        return {
            'cart': {
                'total_items': 0,
                'subtotal': 0,
                'is_empty': True,
                'items': [],
            },
            'cart_total_items': 0,
            'cart_subtotal': 0,
        }