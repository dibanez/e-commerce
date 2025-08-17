"""
API views for cart app.
"""
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.catalog.models import Product
from .models import CartItem
from .services import CartService


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for CartItem model.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.base_price', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_name', 'product_price',
            'quantity', 'unit_price', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'unit_price', 'created_at']


class CartItemCreateSerializer(serializers.Serializer):
    """
    Serializer for creating cart items.
    """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value, is_active=True)
            return product
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or not available")


class CartItemUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating cart item quantity.
    """
    quantity = serializers.IntegerField(min_value=0)


class CartItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for cart items.
    """
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        cart_service = CartService(
            user=self.request.user if self.request.user.is_authenticated else None,
            session=self.request.session
        )
        cart = cart_service.get_cart()
        return cart.items.select_related('product').all()
    
    def create(self, request, *args, **kwargs):
        """
        Add item to cart.
        """
        serializer = CartItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        
        cart_service = CartService(
            user=request.user if request.user.is_authenticated else None,
            session=request.session
        )
        
        try:
            cart_item = cart_service.add_product(product, quantity)
            
            # Return the cart item
            item_serializer = CartItemSerializer(cart_item, context={'request': request})
            return Response(item_serializer.data, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """
        Update cart item quantity.
        """
        cart_item = self.get_object()
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quantity = serializer.validated_data['quantity']
        
        cart_service = CartService(
            user=request.user if request.user.is_authenticated else None,
            session=request.session
        )
        
        try:
            if quantity == 0:
                cart_service.remove_product(cart_item.product)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                cart_service.update_quantity(cart_item.product, quantity)
                
                # Return updated cart item
                cart_item.refresh_from_db()
                item_serializer = CartItemSerializer(cart_item, context={'request': request})
                return Response(item_serializer.data)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Remove item from cart.
        """
        cart_item = self.get_object()
        
        cart_service = CartService(
            user=request.user if request.user.is_authenticated else None,
            session=request.session
        )
        
        cart_service.remove_product(cart_item.product)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get cart summary.
        """
        cart_service = CartService(
            user=request.user if request.user.is_authenticated else None,
            session=request.session
        )
        
        summary = cart_service.get_cart_summary()
        
        # Serialize items
        items_serializer = CartItemSerializer(
            summary['items'], 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'total_items': summary['total_items'],
            'subtotal': summary['subtotal'],
            'is_empty': summary['is_empty'],
            'items': items_serializer.data,
        })
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Clear all items from cart.
        """
        cart_service = CartService(
            user=request.user if request.user.is_authenticated else None,
            session=request.session
        )
        
        cart_service.clear_cart()
        return Response({'message': 'Cart cleared successfully'})