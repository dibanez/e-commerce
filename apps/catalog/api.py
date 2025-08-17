"""
API views for catalog app.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from .models import Product, ProductAttributeValue


class ProductSerializer(ModelSerializer):
    """
    Serializer for Product model.
    """
    attributes = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'sku', 'base_price', 'currency', 'weight',
            'stock_quantity', 'is_active', 'is_featured', 'created_at',
            'attributes', 'primary_image'
        ]
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_attributes(self, obj):
        """
        Get product attributes.
        """
        attribute_values = obj.get_attribute_values()
        return {
            attr_value.attribute.code: attr_value.get_value()
            for attr_value in attribute_values
        }
    
    def get_primary_image(self, obj):
        """
        Get primary image URL.
        """
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Product model (read-only).
    """
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'currency']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['created_at', 'base_price', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        
        # Filter by attribute values
        for key, value in self.request.query_params.items():
            if key.startswith('attr_'):
                attribute_code = key[5:]  # Remove 'attr_' prefix
                queryset = queryset.filter(
                    attribute_values__attribute__code=attribute_code,
                    attribute_values__value_text=value
                )
        
        return queryset.distinct()
    
    @action(detail=True, methods=['get'])
    def attributes(self, request, pk=None):
        """
        Get detailed product attributes.
        """
        product = self.get_object()
        attribute_values = ProductAttributeValue.objects.filter(
            product=product
        ).select_related('attribute', 'value_option').order_by('attribute__sort_order')
        
        attributes = []
        for attr_value in attribute_values:
            attributes.append({
                'name': attr_value.attribute.name,
                'code': attr_value.attribute.code,
                'type': attr_value.attribute.type,
                'value': attr_value.get_value(),
                'display_name': attr_value.value_option.display_name if attr_value.value_option else None,
            })
        
        return Response(attributes)