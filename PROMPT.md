# Prompt Completo para Django E-commerce con Docker

Basándome en todo el proceso de desarrollo y los errores encontrados, aquí está el prompt específico y completo para generar esta aplicación Django e-commerce exitosamente:

## **Prompt Completo para Django E-commerce con Docker**

```
Crea un proyecto Django e-commerce completo con las siguientes especificaciones técnicas. IMPORTANTE: Sigue exactamente este orden y configuración para evitar errores de dependencias y migraciones.

### REQUISITOS TÉCNICOS ESPECÍFICOS

**Stack Base:**
- Django 5.0.8
- PostgreSQL 16 (Alpine)
- Python 3.12
- Docker Compose (sin version field)
- Mailpit para testing de emails

**Dependencias Críticas (requirements.txt en este orden exacto):**
```
Django==5.0.8
psycopg[binary]==3.2.3
python-decouple==3.8
Pillow==10.4.0
django-allauth==0.63.6
django-fsm==2.8.1
djangorestframework==3.15.2
django-filter==24.2
django-debug-toolbar==4.4.6
pytest==8.3.2
pytest-django==4.8.0
pytest-cov==5.0.0
factory-boy==3.3.1
ruff==0.6.2
black==24.8.0
isort==5.13.2
mypy==1.11.1
django-stubs==5.0.4
gunicorn==23.0.0
whitenoise==6.7.0
```

### ARQUITECTURA DE APLICACIONES

**ORDEN CRÍTICO en INSTALLED_APPS:**
```python
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth', 
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

LOCAL_APPS = [
    'apps.core',
    'apps.users',      # DEBE ir antes de allauth
    'apps.catalog',
    'apps.cart',
    'apps.orders', 
    'apps.payments',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'django_fsm',
    'debug_toolbar',
]

ALLAUTH_APPS = [
    'allauth',
    'allauth.account', 
    'allauth.socialaccount',
]

# ORDEN FINAL CRÍTICO:
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS + ALLAUTH_APPS
```

### MODELOS DE DATOS ESPECÍFICOS

**1. Users App (apps/users/models.py):**
- Custom User model con EMAIL como USERNAME_FIELD
- UserProfile con OneToOne al User
- Address model con ForeignKey al User (NO al UserProfile)
- Managers personalizados para User

**2. Catalog App (apps/catalog/models.py):**
- Sistema EAV completo para atributos dinámicos
- Category con self-referencing parent
- Product con category ForeignKey
- ProductAttribute para definir tipos de atributos
- ProductAttributeOption para opciones predefinidas
- ProductAttributeValue para valores polimórficos (text, integer, decimal, boolean, date)
- ProductImage con ordering

**3. Cart App (apps/cart/models.py):**
- Cart con user y session_key opcionales
- Check constraint: user_id IS NOT NULL OR session_key IS NOT NULL
- CartItem con unique_together (cart, product)

**4. Orders App (apps/orders/models.py):**
- Order con UUID primary key
- FSMField para status con estados: pending, processing, shipped, delivered, cancelled
- Campos completos de billing y shipping
- OrderItem para line items
- OrderStatusHistory para audit trail

**5. Payments App (apps/payments/models.py):**
- Sistema de plugins con base class abstracta
- Payment model con provider_name
- Transaction model para logs

### CONFIGURACIÓN DOCKER CRÍTICA

**docker-compose.yml (SIN version field):**
```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: postgres  
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  mailpit:
    image: axllent/mailpit:latest
    ports:
      - "8025:8025"
      - "1025:1025"

  web:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.dev
```

**Dockerfile:**
- Multi-stage build
- Usuario django no-root
- Permisos correctos para /app/logs, /app/staticfiles, /app/mediafiles

### CONFIGURACIONES ESPECÍFICAS

**Settings base:**
```python
AUTH_USER_MODEL = 'users.User'
SITE_ID = 1

# AllAuth config
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Payment providers
PAYMENT_PROVIDERS = [
    'apps.payments.providers.dummy.DummyProvider',
]
```

**URLs principales:**
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.core.urls')),
    path('catalog/', include('apps.catalog.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('payments/', include('apps.payments.urls')),
    path('api/', include('apps.core.api_urls')),
]
```

### ORDEN DE MIGRACIÓN CRÍTICO

**NUNCA crear migraciones hasta que:**
1. Todos los modelos estén definidos
2. INSTALLED_APPS esté en el orden correcto
3. AUTH_USER_MODEL esté configurado

**Proceso de migración:**
```bash
# 1. Crear migraciones para users PRIMERO
python manage.py makemigrations users

# 2. Aplicar migración de users
python manage.py migrate users

# 3. Crear migraciones para allauth
python manage.py migrate

# 4. Crear migraciones para el resto
python manage.py makemigrations catalog cart orders payments

# 5. Aplicar todas las migraciones
python manage.py migrate
```

### ADMIN CONFIGURATION

**Configurar AddressInline en UserAdmin (NO en UserProfileAdmin):**
```python
class AddressInline(admin.TabularInline):
    model = Address
    extra = 0

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [AddressInline]
```

### API CONFIGURATION

**En catalog/api.py asegurar:**
```python
from rest_framework import filters, serializers, viewsets

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductSerializer
```

### EVITAR ESTOS ERRORES ESPECÍFICOS:

1. **NO incluir payments URLs en dos lugares** (urls.py y api_urls.py)
2. **NO usar AUTH_USER_MODEL después de migrar**
3. **NO crear AddressInline en UserProfileAdmin** (va en UserAdmin)
4. **NO olvidar QuerySet en ViewSets**
5. **NO usar version field en docker-compose.yml**
6. **INCLUIR django-filter en requirements.txt**
7. **CREAR migrations directories con permisos correctos**

### TEMPLATES Y FRONTEND

- Base template con Tailwind CSS
- Templates para allauth (login, signup, email_confirm)
- Error pages (404, 500)
- Responsive design
- JavaScript para cart functionality

### TESTING

- Pytest configurado
- Factory Boy para fixtures
- Coverage >85%
- Tests para todos los modelos y vistas principales

### DEPLOYMENT READY

- Gunicorn como WSGI server
- WhiteNoise para static files
- Environment variables con python-decouple
- Logging configurado para desarrollo y producción
- Settings separados (base, dev, prod)

Esta configuración garantiza un despliegue exitoso sin errores de dependencias o migraciones.
```

## **Comandos de Inicialización Post-Generación:**

```bash
# 1. Construir contenedores
docker compose build

# 2. Iniciar servicios
docker compose up -d

# 3. Verificar que web esté funcionando
docker compose ps

# 4. Crear superuser
docker compose run --rm web python manage.py createsuperuser --email admin@localhost

# 5. Verificar aplicación
curl http://localhost:8000/
curl http://localhost:8000/admin/
```

## **Errores Específicos Resueltos Durante el Desarrollo:**

### 1. **Error de Dependencia Faltante**
```
ModuleNotFoundError: No module named 'django_filter'
```
**Solución:** Agregar `django-filter==24.2` a requirements.txt

### 2. **Error de Import en API**
```
NameError: name 'serializers' is not defined
```
**Solución:** Importar correctamente `from rest_framework import filters, serializers, viewsets`

### 3. **Error de ViewSet sin QuerySet**
```
AssertionError: 'ProductViewSet' should either include a `queryset` attribute
```
**Solución:** Agregar `queryset = Product.objects.filter(is_active=True).select_related('category')`

### 4. **Error de Configuración de Admin**
```
<class 'apps.users.admin.AddressInline'>: (admin.E202) fk_name 'user' is not a ForeignKey to 'apps.users.UserProfile'
```
**Solución:** Mover AddressInline de UserProfileAdmin a UserAdmin

### 5. **Error de Namespace Duplicado**
```
django.core.exceptions.ImproperlyConfigured: The included URLconf 'apps.payments.urls' does not appear to have any patterns named 'payments'
```
**Solución:** Eliminar include duplicado de payments en api_urls.py

### 6. **Error de Historial de Migraciones Inconsistente**
```
InconsistentMigrationHistory: Migration admin.0001_initial is applied before its dependency users.0001_initial
```
**Solución:** Resetear base de datos y aplicar migraciones en orden correcto con apps en INSTALLED_APPS ordenadas correctamente

### 7. **Error de Templates de Debug Toolbar**
```
TemplateDoesNotExist: debug_toolbar/base.html
```
**Solución:** Agregar `django-debug-toolbar==4.4.6` a requirements.txt

### 8. **Error de Tablas No Existentes**
```
ProgrammingError: relation "catalog_category" does not exist
```
**Solución:** Crear y aplicar migraciones para todas las apps: catalog, cart, orders, payments

### 9. **Error de Filtro de Template No Existente**
```
TemplateSyntaxError: Invalid filter: 'mul'
```
**Solución:** Crear filtro personalizado en `apps/cart/templatetags/cart_filters.py`:
```python
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiplies the value by the argument."""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, AttributeError):
        return 0

@register.filter
def currency(value):
    """Formats a value as currency."""
    try:
        return f"${Decimal(str(value)):.2f}"
    except (ValueError, TypeError, AttributeError):
        return "$0.00"
```

Y cargar en templates con: `{% load cart_filters %}`

### 10. **Error de Template No Existente**
```
TemplateDoesNotExist at /orders/
orders/order_list.html
```
**Solución:** Crear todos los templates necesarios en la estructura correcta:
- `templates/orders/order_list.html` - Lista de pedidos del usuario
- `templates/orders/order_detail.html` - Detalle completo del pedido
- `templates/cart/cart_detail.html` - Vista del carrito
- `templates/catalog/product_list.html` - Lista de productos
- `templates/catalog/product_detail.html` - Detalle de producto

**Estructura de templates requerida:**
```
templates/
├── account/           # Templates de allauth
├── cart/             # Templates del carrito
├── catalog/          # Templates del catálogo
├── core/             # Templates principales
├── errors/           # Páginas de error (404, 500)
└── orders/           # Templates de pedidos
```

### 11. **Error de Sintaxis de URLs en Templates de Allauth**
```
TemplateSyntaxError: Could not parse the remainder: ':home' from 'core:home'
```
**Problema:** Templates de allauth con sintaxis incorrecta en tags URL (falta de comillas)
**Solución:** Corregir todos los tags URL en templates de allauth:
- Cambiar `{% url account_login %}` por `{% url 'account_login' %}`
- Cambiar `{% url core:home %}` por `{% url 'core:home' %}`
- Verificar sintaxis en: login.html, signup.html, password_reset.html, email_confirm.html
- Usar docker exec con permisos root para crear/editar templates

**Templates de allauth creados con diseño Tailwind CSS:**
- `account/login.html` - Inicio de sesión con diseño moderno
- `account/signup.html` - Registro de usuario con validación
- `account/password_reset.html` - Restablecimiento de contraseña
- `account/password_reset_done.html` - Confirmación de envío de email
- `account/password_reset_from_key.html` - Formulario nueva contraseña
- `account/password_reset_from_key_done.html` - Confirmación de cambio
- `account/logout.html` - Confirmación de cierre de sesión
- `account/email.html` - Gestión de direcciones de email
- `account/email_confirm.html` - Confirmación de email

### 12. **Error de Falta de Diseño CSS en Vistas de Account**
```
las views que estan en /accounts/ no tienen diseño css
```
**Problema:** Las vistas de allauth (login, signup, password reset, etc.) carecían de diseño CSS consistente con la aplicación
**Solución Completa:**

1. **Crear templates de allauth con Tailwind CSS:**
```bash
# Usar permisos root para crear templates
docker compose exec -u root web bash -c 'cat > /app/templates/account/template.html'
```

2. **Características de diseño implementadas:**
- Diseño responsive con Tailwind CSS
- Iconos SVG para cada función (login, signup, reset)
- Formularios centrados con máximo ancho de md
- Estados de validación con mensajes de error rojos
- Botones con efectos hover y focus
- Navegación consistente de vuelta al inicio
- Colores de marca (blue-600, green-600, red-600)
- Espaciado y tipografía coherente

3. **Templates específicos creados:**
- `/templates/account/login.html` - Formulario de inicio de sesión
- `/templates/account/signup.html` - Formulario de registro
- `/templates/account/password_reset.html` - Solicitud de restablecimiento
- `/templates/account/password_reset_done.html` - Confirmación de envío
- `/templates/account/password_reset_from_key.html` - Nueva contraseña
- `/templates/account/password_reset_from_key_done.html` - Cambio exitoso
- `/templates/account/logout.html` - Confirmación de logout
- `/templates/account/email.html` - Gestión de emails
- `/templates/account/email_confirm.html` - Confirmación de email

4. **Verificación de funcionamiento:**
```bash
# Verificar que todas las páginas respondan correctamente
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/accounts/login/     # 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/accounts/signup/    # 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/accounts/password/reset/ # 200
```

**Resultado:** Todas las vistas de `/accounts/` ahora tienen diseño CSS profesional y consistente con el resto de la aplicación.

### 13. **Error RelatedObjectDoesNotExist en Admin ProductAttributeValue**
```
RelatedObjectDoesNotExist at /admin/catalog/product/add/
ProductAttributeValue has no attribute.
```
**Problema:** Error en admin inline de ProductAttributeValue al intentar acceder a `instance.attribute` cuando no existe relación aún
**Causa Raíz:** En el `ProductAttributeValueInline.get_formset()`, el código intentaba acceder a `self.instance.attribute` en formularios vacíos (cuando se crea un producto nuevo), pero la instancia no tiene atributo asignado aún.

**Solución:**
```python
# En apps/catalog/admin.py - ProductAttributeValueInline
def get_formset(self, request, obj=None, **kwargs):
    formset = super().get_formset(request, obj, **kwargs)
    
    class CustomForm(formset.form):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            # ANTES (causaba error):
            # if self.instance and self.instance.attribute:
            
            # DESPUÉS (corregido):
            if self.instance and self.instance.pk and hasattr(self.instance, 'attribute_id') and self.instance.attribute_id:
                try:
                    attr_type = self.instance.attribute.type
                    # ... resto del código para ocultar campos
                except (AttributeError, ProductAttribute.DoesNotExist):
                    # Si attribute no existe aún, no ocultar campos
                    pass
```

**Verificación:**
```bash
# Probar acceso a admin sin errores
docker compose exec web python manage.py shell -c "
from django.test import Client
from django.contrib.auth import get_user_model
client = Client()
user = get_user_model().objects.filter(is_superuser=True).first()
client.force_login(user)
response = client.get('/admin/catalog/product/add/')
print('Status:', response.status_code)  # Debe ser 200
"
```

**Resultado:** El admin de productos ahora carga correctamente sin errores RelatedObjectDoesNotExist.

### 14. **Error TemplateDoesNotExist para Category Detail**
```
TemplateDoesNotExist at /catalog/category/informatica/
catalog/category_detail.html
```
**Problema:** Falta el template para mostrar el detalle de categorías
**Causa:** El view `CategoryDetailView` está configurado en `catalog/views.py` y la URL en `catalog/urls.py`, pero no existe el template correspondiente.

**Solución:**
Crear `templates/catalog/category_detail.html` con diseño completo que incluya:

1. **Breadcrumb navigation** con categorías padre
2. **Header de categoría** con nombre, descripción e imagen
3. **Sección de subcategorías** en grid responsive
4. **Grid de productos** con:
   - Imágenes de productos
   - Información de precios y stock
   - Badges de estado (sin stock, destacado)
   - Botón añadir al carrito
5. **Funcionalidad de ordenamiento** (precio, nombre, fecha)
6. **Paginación** para grandes catálogos
7. **Estado vacío** cuando no hay productos
8. **JavaScript** para añadir al carrito y notificaciones

**Verificación:**
```bash
# Verificar que la página carga correctamente
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/catalog/category/informatica/  # 200

# Verificar que el título se renderiza
curl -s http://localhost:8000/catalog/category/informatica/ | grep -o "<title>[^<]*"
# Output: <title>Informatica - Categoría
```

**Template Features Implementadas:**
- Diseño responsive con Tailwind CSS
- Breadcrumb navigation jerárquico
- Grid de subcategorías con contadores
- Grid de productos con imágenes y precios
- Add to cart functionality con AJAX
- Sort/filter controls
- Pagination support
- Empty states
- Stock status indicators
- Featured product badges

**Resultado:** Las páginas de categorías ahora muestran correctamente productos y subcategorías con navegación intuitiva.

### 15. **Error InvalidOperation Decimal ConversionSyntax en Cart**
```
InvalidOperation at /cart/
[<class 'decimal.ConversionSyntax'>]
```
**Problema:** Error de conversión decimal en templates que usan filtros custom `mul` y `currency`
**Causa Raíz:** 
1. Templates estaban encadenando `floatformat:2` antes de `mul:0.21`, causando conversión de strings formateados a Decimal
2. Filtros custom no capturaban la excepción `decimal.InvalidOperation`
3. La propiedad `subtotal` del modelo Cart podía retornar `None` en casos edge

**Solución:**

1. **Actualizar filtros custom** en `apps/cart/templatetags/cart_filters.py`:
```python
from decimal import Decimal, InvalidOperation

@register.filter
def mul(value, arg):
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
```

2. **Corregir orden de filtros en templates**:
```django
<!-- ANTES (causaba error): -->
{{ cart_summary.subtotal|floatformat:2|mul:0.21 }}

<!-- DESPUÉS (correcto): -->
{{ cart_summary.subtotal|mul:0.21|floatformat:2 }}
```

3. **Proteger subtotal en modelo Cart**:
```python
@property
def subtotal(self) -> Decimal:
    total = sum(item.total_price for item in self.items.all())
    return total if total is not None else Decimal('0.00')
```

**Templates corregidos:**
- `templates/cart/cart_detail.html` - IVA calculation y total
- `templates/orders/checkout.html` - IVA y total calculations
- `templates/orders/order_detail.html` - Ya era correcto

**Verificación:**
```bash
# Verificar que el carrito carga sin errores
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/cart/  # 200
```

**Resultado:** Todas las páginas con cálculos de carrito funcionan correctamente sin errores de conversión decimal.

### 16. **Error VariableDoesNotExist search_query en Templates**
```
DEBUG Exception while resolving variable 'search_query' in template 'orders/checkout.html'
VariableDoesNotExist: Failed lookup for key [search_query]
```
**Problema:** Template base.html usa variable `search_query` que no está disponible en todos los contextos
**Causa Raíz:** El template base incluye un formulario de búsqueda que espera la variable `search_query`, pero no todas las vistas la proporcionan en su contexto.

**Solución:**
Crear un context processor global para proporcionar `search_query` a todos los templates:

1. **Crear context processor** en `apps/core/context_processors.py`:
```python
def search(request):
    """
    Add search query to template context.
    """
    return {
        'search_query': request.GET.get('q', ''),
    }
```

2. **Registrar en settings** (`config/settings/base.py`):
```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.cart.context_processors.cart',
                'apps.core.context_processors.search',  # Añadir esta línea
            ],
        },
    },
]
```

3. **Reiniciar aplicación** para cargar el nuevo context processor:
```bash
docker compose restart web
```

**Verificación:**
```bash
# Probar checkout con carrito y usuario autenticado
docker compose exec web python manage.py shell -c "
from django.test import Client
from django.contrib.auth import get_user_model
client = Client()
user = get_user_model().objects.filter(is_superuser=True).first()
client.force_login(user)
response = client.get('/orders/checkout/')
print('Status:', response.status_code)  # Debe ser 200
"
```

**Resultado:** Todas las páginas ahora tienen acceso a `search_query` sin errores de contexto.

### 17. **Error ConfigError: Couldn't read config file pyproject.toml**
```
coverage.exceptions.ConfigError: Couldn't read config file pyproject.toml: Option [tool.coverage.run]source is not a list: 'apps'
```
**Problema:** Configuración incorrecta en pyproject.toml para coverage - el campo `source` debe ser una lista
**Causa Raíz:** El valor `source = "apps"` estaba configurado como string en lugar de lista.

**Solución:**
```toml
# ANTES (causaba error):
[tool.coverage.run]
source = "apps"

# DESPUÉS (correcto):
[tool.coverage.run]
source = ["apps"]
```

**Verificación:**
```bash
# Verificar que pytest funciona sin errores de configuración
docker compose exec web python -m pytest --version
docker compose exec web python -m pytest tests/ -v
```

**Resultado:** Los tests se ejecutan correctamente sin errores de configuración de coverage.

### 18. **Error Test Fallando: DummyProvider success_rate Override**
```
AssertionError: assert not True
 +  where True = PaymentInitResult(..., success=True, error_message=None).success
```
**Problema:** Test fallando porque configuración de Django settings sobrescribía la configuración de test
**Causa Raíz:** El `DummyProvider` tenía lógica donde Django settings (`DUMMY_PAYMENT_SUCCESS_RATE=100`) sobrescribía la configuración pasada en el constructor del test (`{'success_rate': 0}`).

**Solución:**
```python
# ANTES (settings sobrescribían config):
def __init__(self, config=None):
    super().__init__(config)
    self.success_rate = self.config.get('success_rate', 100)
    if hasattr(settings, 'DUMMY_PAYMENT_SUCCESS_RATE'):
        self.success_rate = int(settings.DUMMY_PAYMENT_SUCCESS_RATE)

# DESPUÉS (config puede sobrescribir settings):
def __init__(self, config=None):
    super().__init__(config)
    default_success_rate = 100
    if hasattr(settings, 'DUMMY_PAYMENT_SUCCESS_RATE'):
        default_success_rate = int(settings.DUMMY_PAYMENT_SUCCESS_RATE)
    self.success_rate = self.config.get('success_rate', default_success_rate)
```

**También se corrigió el rango de random para incluir 0:**
```python
# ANTES:
should_succeed = random.randint(1, 100) <= self.success_rate
# DESPUÉS:
should_succeed = random.randint(0, 100) <= self.success_rate
```

**Verificación:**
```bash
# Verificar que todos los tests pasan
docker compose exec web python -m pytest tests/ -v
```

**Resultado:** Todos los tests pasan correctamente, incluyendo el test de fallo simulado con `success_rate=0`.

Este prompt incluye todas las lecciones aprendidas de los errores encontrados durante el desarrollo y garantiza una implementación exitosa desde el primer intento.