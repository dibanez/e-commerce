"""
Forms for orders app.
"""
from django import forms
from django.core.validators import RegexValidator


class CheckoutForm(forms.Form):
    """
    Checkout form for billing and shipping information.
    """
    # Billing information
    billing_first_name = forms.CharField(
        label='Nombre',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        })
    )
    billing_last_name = forms.CharField(
        label='Apellidos',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        })
    )
    billing_company = forms.CharField(
        label='Empresa',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Empresa (opcional)'
        })
    )
    billing_address_line_1 = forms.CharField(
        label='Dirección',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dirección'
        })
    )
    billing_address_line_2 = forms.CharField(
        label='Dirección 2',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apartamento, suite, etc. (opcional)'
        })
    )
    billing_city = forms.CharField(
        label='Ciudad',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad'
        })
    )
    billing_state = forms.CharField(
        label='Provincia',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Provincia'
        })
    )
    billing_postal_code = forms.CharField(
        label='Código Postal',
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\d{5}$',
                message='El código postal debe tener 5 dígitos'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '28001'
        })
    )
    billing_country = forms.ChoiceField(
        label='País',
        choices=[
            ('ES', 'España'),
            ('FR', 'Francia'),
            ('IT', 'Italia'),
            ('PT', 'Portugal'),
        ],
        initial='ES',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    billing_phone = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+34 600 000 000'
        })
    )
    
    # Shipping information
    shipping_same_as_billing = forms.BooleanField(
        label='La dirección de envío es la misma que la de facturación',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'same-address'
        })
    )
    
    shipping_first_name = forms.CharField(
        label='Nombre',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        })
    )
    shipping_last_name = forms.CharField(
        label='Apellidos',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        })
    )
    shipping_company = forms.CharField(
        label='Empresa',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Empresa (opcional)'
        })
    )
    shipping_address_line_1 = forms.CharField(
        label='Dirección',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dirección'
        })
    )
    shipping_address_line_2 = forms.CharField(
        label='Dirección 2',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apartamento, suite, etc. (opcional)'
        })
    )
    shipping_city = forms.CharField(
        label='Ciudad',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad'
        })
    )
    shipping_state = forms.CharField(
        label='Provincia',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Provincia'
        })
    )
    shipping_postal_code = forms.CharField(
        label='Código Postal',
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\d{5}$',
                message='El código postal debe tener 5 dígitos'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '28001'
        })
    )
    shipping_country = forms.ChoiceField(
        label='País',
        choices=[
            ('ES', 'España'),
            ('FR', 'Francia'),
            ('IT', 'Italia'),
            ('PT', 'Portugal'),
        ],
        initial='ES',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    shipping_phone = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+34 600 000 000'
        })
    )
    
    # Additional fields
    guest_email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com'
        })
    )
    notes = forms.CharField(
        label='Notas del pedido',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notas especiales sobre tu pedido...'
        })
    )
    terms_accepted = forms.BooleanField(
        label='Acepto los términos y condiciones',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    newsletter_signup = forms.BooleanField(
        label='Quiero recibir ofertas y noticias por email',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        shipping_same_as_billing = cleaned_data.get('shipping_same_as_billing')
        
        # If shipping is not same as billing, validate shipping fields
        if not shipping_same_as_billing:
            shipping_required_fields = [
                'shipping_first_name',
                'shipping_last_name',
                'shipping_address_line_1',
                'shipping_city',
                'shipping_state',
                'shipping_postal_code',
                'shipping_country'
            ]
            
            for field in shipping_required_fields:
                if not cleaned_data.get(field):
                    field_name = field.replace('shipping_', '').replace('_', ' ').title()
                    self.add_error(field, f'{field_name} es obligatorio cuando la dirección de envío es diferente')
        
        return cleaned_data

    def get_billing_data(self):
        """
        Extract billing data from cleaned form data.
        """
        return {
            'first_name': self.cleaned_data['billing_first_name'],
            'last_name': self.cleaned_data['billing_last_name'],
            'company': self.cleaned_data['billing_company'],
            'address_line_1': self.cleaned_data['billing_address_line_1'],
            'address_line_2': self.cleaned_data['billing_address_line_2'],
            'city': self.cleaned_data['billing_city'],
            'state': self.cleaned_data['billing_state'],
            'postal_code': self.cleaned_data['billing_postal_code'],
            'country': self.cleaned_data['billing_country'],
            'phone': self.cleaned_data['billing_phone'],
        }

    def get_shipping_data(self):
        """
        Extract shipping data from cleaned form data.
        """
        if self.cleaned_data.get('shipping_same_as_billing'):
            # Use billing data for shipping
            return self.get_billing_data()
        
        return {
            'first_name': self.cleaned_data['shipping_first_name'],
            'last_name': self.cleaned_data['shipping_last_name'],
            'company': self.cleaned_data['shipping_company'],
            'address_line_1': self.cleaned_data['shipping_address_line_1'],
            'address_line_2': self.cleaned_data['shipping_address_line_2'],
            'city': self.cleaned_data['shipping_city'],
            'state': self.cleaned_data['shipping_state'],
            'postal_code': self.cleaned_data['shipping_postal_code'],
            'country': self.cleaned_data['shipping_country'],
            'phone': self.cleaned_data['shipping_phone'],
        }

    def get_additional_data(self):
        """
        Extract additional data from cleaned form data.
        """
        return {
            'guest_email': self.cleaned_data.get('guest_email'),
            'notes': self.cleaned_data.get('notes', ''),
            'terms_accepted': self.cleaned_data.get('terms_accepted', False),
            'newsletter_signup': self.cleaned_data.get('newsletter_signup', False),
        }