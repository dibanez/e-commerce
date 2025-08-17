"""
API views for orders app.
"""
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.services import CartService
from .forms import CheckoutForm
from .services import OrderService


class CheckoutSerializer(serializers.Serializer):
    """
    Serializer for checkout API.
    """
    # Billing information
    billing_first_name = serializers.CharField(max_length=50)
    billing_last_name = serializers.CharField(max_length=50)
    billing_company = serializers.CharField(max_length=100, required=False, allow_blank=True)
    billing_address_line_1 = serializers.CharField(max_length=255)
    billing_address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    billing_city = serializers.CharField(max_length=100)
    billing_state = serializers.CharField(max_length=100)
    billing_postal_code = serializers.CharField(max_length=20)
    billing_country = serializers.CharField(max_length=2, default='ES')
    billing_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Shipping information
    shipping_same_as_billing = serializers.BooleanField(default=True)
    shipping_first_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    shipping_last_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    shipping_company = serializers.CharField(max_length=100, required=False, allow_blank=True)
    shipping_address_line_1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    shipping_address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    shipping_city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    shipping_state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    shipping_postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    shipping_country = serializers.CharField(max_length=2, required=False, allow_blank=True)
    shipping_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Additional fields
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    terms_accepted = serializers.BooleanField(default=False)
    newsletter_signup = serializers.BooleanField(default=False)
    
    # Payment
    payment_provider = serializers.CharField(max_length=50)
    
    def validate(self, data):
        """
        Validate checkout data.
        """
        # Validate terms acceptance
        if not data.get('terms_accepted'):
            raise serializers.ValidationError(
                {'terms_accepted': 'You must accept the terms and conditions'}
            )
        
        # Validate shipping address if different from billing
        if not data.get('shipping_same_as_billing'):
            shipping_required_fields = [
                'shipping_first_name', 'shipping_last_name', 'shipping_address_line_1',
                'shipping_city', 'shipping_state', 'shipping_postal_code'
            ]
            
            for field in shipping_required_fields:
                if not data.get(field):
                    field_name = field.replace('shipping_', '').replace('_', ' ').title()
                    raise serializers.ValidationError(
                        {field: f'{field_name} is required when shipping address is different'}
                    )
        
        return data
    
    def get_billing_data(self):
        """
        Extract billing data from validated data.
        """
        return {
            'first_name': self.validated_data['billing_first_name'],
            'last_name': self.validated_data['billing_last_name'],
            'company': self.validated_data.get('billing_company', ''),
            'address_line_1': self.validated_data['billing_address_line_1'],
            'address_line_2': self.validated_data.get('billing_address_line_2', ''),
            'city': self.validated_data['billing_city'],
            'state': self.validated_data['billing_state'],
            'postal_code': self.validated_data['billing_postal_code'],
            'country': self.validated_data.get('billing_country', 'ES'),
            'phone': self.validated_data.get('billing_phone', ''),
        }
    
    def get_shipping_data(self):
        """
        Extract shipping data from validated data.
        """
        if self.validated_data.get('shipping_same_as_billing'):
            return self.get_billing_data()
        
        return {
            'first_name': self.validated_data.get('shipping_first_name', ''),
            'last_name': self.validated_data.get('shipping_last_name', ''),
            'company': self.validated_data.get('shipping_company', ''),
            'address_line_1': self.validated_data.get('shipping_address_line_1', ''),
            'address_line_2': self.validated_data.get('shipping_address_line_2', ''),
            'city': self.validated_data.get('shipping_city', ''),
            'state': self.validated_data.get('shipping_state', ''),
            'postal_code': self.validated_data.get('shipping_postal_code', ''),
            'country': self.validated_data.get('shipping_country', 'ES'),
            'phone': self.validated_data.get('shipping_phone', ''),
        }
    
    def get_additional_data(self):
        """
        Extract additional data from validated data.
        """
        return {
            'guest_email': self.validated_data.get('guest_email'),
            'notes': self.validated_data.get('notes', ''),
            'terms_accepted': self.validated_data.get('terms_accepted', False),
            'newsletter_signup': self.validated_data.get('newsletter_signup', False),
        }


class CheckoutAPIView(APIView):
    """
    API view for checkout process.
    """
    
    def post(self, request):
        """
        Process checkout and create order.
        """
        # Check if cart is not empty
        cart_service = CartService(
            user=request.user if request.user.is_authenticated else None,
            session=request.session
        )
        cart_summary = cart_service.get_cart_summary()
        
        if cart_summary['is_empty']:
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate checkout data
        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create order
            order = OrderService.checkout_flow(
                user=request.user if request.user.is_authenticated else None,
                session=request.session,
                billing_data=serializer.get_billing_data(),
                shipping_data=serializer.get_shipping_data(),
                additional_data=serializer.get_additional_data()
            )
            
            # Initiate payment
            from apps.payments.services import PaymentService
            
            provider_code = serializer.validated_data['payment_provider']
            
            return_url = request.build_absolute_uri(f'/payments/return/{order.number}/{provider_code}/')
            notify_url = request.build_absolute_uri(f'/api/payments/webhook/{provider_code}/')
            
            payment_result = PaymentService.initiate_payment(
                order=order,
                provider_code=provider_code,
                return_url=return_url,
                notify_url=notify_url
            )
            
            if not payment_result['success']:
                return Response(
                    {
                        'error': 'Payment initiation failed',
                        'details': payment_result.get('error')
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Return order and payment information
            return Response({
                'success': True,
                'order_number': order.number,
                'order_id': str(order.id),
                'payment_id': payment_result['payment_id'],
                'redirect_url': payment_result.get('redirect_url'),
                'grand_total': float(order.grand_total),
                'currency': order.currency,
            }, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Checkout failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )