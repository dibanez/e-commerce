# E-Commerce Django con Arquitectura Limpia

Aplicación web de comercio electrónico desarrollada con Django 5.x, PostgreSQL y Docker, siguiendo principios de arquitectura limpia y las mejores prácticas de desarrollo.

## 🚀 Características

- **Autenticación por email** con verificación y recuperación de contraseña (django-allauth)
- **Catálogo de productos** con categorías jerárquicas y **atributos dinámicos tipados** (EAV)
- **Carrito de compras** basado en sesión con migración a usuario autenticado
- **Sistema de checkout** con captura de direcciones de envío/facturación
- **Sistema de pagos por plugins** fácilmente extensible (incluye DummyProvider para desarrollo)
- **Gestión de pedidos** con máquina de estados (django-fsm)
- **Panel de administración** completo para gestión de productos y atributos
- **Entorno dockerizado** con PostgreSQL y Mailpit para emails en desarrollo
- **Tests automatizados** con pytest y cobertura >85%
- **Calidad de código** con ruff, black, isort y mypy

## 📋 Requisitos

- Docker y Docker Compose
- Make (opcional, para usar comandos simplificados)
- Git

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd ecommerce-django
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env.dev
```

Editar `.env.dev` si es necesario (las configuraciones por defecto funcionan para desarrollo).

### 3. Construir y ejecutar con Docker

```bash
# Con Make
make build
make up

# O directamente con Docker Compose
docker-compose build
docker-compose up
```

La aplicación estará disponible en:
- **Web**: http://localhost:8000
- **Mailpit** (UI de emails): http://localhost:8025
- **Admin Django**: http://localhost:8000/admin/

### 4. Crear superusuario (opcional)

```bash
make createsuperuser
# O: docker-compose exec web python manage.py createsuperuser
```

## 🏗️ Arquitectura

### Estructura del Proyecto

```
.
├── apps/                      # Aplicaciones Django
│   ├── users/                # Autenticación y usuarios
│   ├── catalog/              # Productos y categorías
│   ├── cart/                 # Carrito de compras
│   ├── orders/               # Gestión de pedidos
│   ├── payments/             # Sistema de pagos
│   └── core/                 # Utilidades comunes
├── config/                   # Configuración Django
│   └── settings/
│       ├── base.py          # Settings base
│       ├── dev.py           # Settings desarrollo
│       └── prod.py          # Settings producción
├── docker/                   # Archivos Docker
├── static/                   # Archivos estáticos
├── templates/               # Plantillas HTML
├── tests/                   # Tests
└── docker-compose.yml       # Configuración Docker Compose
```

### Sistema de Atributos Dinámicos (EAV)

El sistema permite definir atributos personalizados para productos con tipos:
- `text`: Texto libre
- `integer`: Números enteros
- `decimal`: Números decimales
- `boolean`: Verdadero/Falso
- `date`: Fechas
- `enum`: Lista de opciones predefinidas

### Sistema de Pagos por Plugins

Arquitectura extensible para añadir nuevos métodos de pago:

1. **Interfaz PaymentProvider**: Define los métodos que debe implementar cada proveedor
2. **Registry**: Sistema de registro dinámico de proveedores
3. **DummyProvider**: Implementación de ejemplo para desarrollo

#### Añadir un nuevo proveedor de pagos

1. Crear una clase que herede de `PaymentProvider`:

```python
# apps/payments/providers/stripe.py
from apps.payments.base import PaymentProvider, PaymentInitResult

class StripeProvider(PaymentProvider):
    code = "stripe"
    display_name = "Stripe"
    
    def start_payment(self, order, return_url, notify_url):
        # Implementar lógica de Stripe
        pass
    
    def handle_webhook(self, request):
        # Procesar webhook de Stripe
        pass
```

2. Registrar en settings:

```python
PAYMENT_PROVIDERS = [
    "apps.payments.providers.dummy.DummyProvider",
    "apps.payments.providers.stripe.StripeProvider",
]
```

## 📝 Comandos Make

```bash
make build          # Construir imagen Docker
make up            # Iniciar servicios
make down          # Detener servicios
make logs          # Ver logs
make shell         # Shell de Django
make migrate       # Ejecutar migraciones
make test          # Ejecutar tests
make lint          # Ejecutar linters
make fmt           # Formatear código
make createsuperuser # Crear superusuario
```

## 🧪 Tests

Ejecutar tests con cobertura:

```bash
make test
# O: docker-compose exec web pytest --cov=apps --cov-report=html
```

Los tests cubren:
- Registro y verificación de email
- Creación de productos con atributos dinámicos
- Flujo completo: carrito → checkout → pago
- Webhooks de pagos
- Estados de pedidos con FSM

## 🔧 Desarrollo

### Flujo de trabajo típico

1. **Registro de usuario**:
   - Acceder a `/accounts/signup/`
   - Registrarse con email
   - Verificar email en Mailpit (http://localhost:8025)
   - Activar cuenta

2. **Gestión de productos** (como admin):
   - Crear categorías y productos
   - Definir atributos personalizados
   - Asignar valores a productos

3. **Compra**:
   - Navegar catálogo
   - Añadir al carrito
   - Checkout con direcciones
   - Pagar con DummyProvider
   - Ver pedido completado

### Variables de entorno principales

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.dev
DATABASE_URL=postgres://postgres:postgres@db:5432/app
EMAIL_HOST=mailpit
EMAIL_PORT=1025
ALLOWED_HOSTS=*
```

## 🚀 Despliegue a Producción

1. Configurar variables de entorno de producción
2. Usar `config.settings.prod`
3. Configurar servidor web (Gunicorn/uWSGI + Nginx)
4. Configurar base de datos PostgreSQL
5. Configurar servicio de email real
6. Ejecutar `collectstatic` para archivos estáticos
7. Configurar SSL/TLS

## 📚 API Endpoints

### Productos
- `GET /api/products/` - Listar productos con filtros
- `GET /api/products/<id>/` - Detalle de producto

### Carrito
- `POST /api/cart/items/` - Añadir item
- `PATCH /api/cart/items/<id>/` - Actualizar cantidad
- `DELETE /api/cart/items/<id>/` - Eliminar item

### Checkout
- `POST /api/checkout/` - Procesar checkout

### Pagos
- `POST /api/payments/webhook/<provider>/` - Webhook de proveedor

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

## 🆘 Soporte

Para reportar bugs o solicitar features, abrir un issue en GitHub.