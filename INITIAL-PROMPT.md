Eres un/a experto/a en Django y arquitectura limpia. Genera un PROYECTO COMPLETO listo para ejecutar con Docker Compose. El resultado debe incluir TODO el código, configuración y tests. Lenguaje de comentarios y README en español; nombres de clases/métodos/código en inglés.

# Objetivo
Aplicación web en Django con:
- Registro e inicio de sesión por email (con verificación de email) y recuperación de contraseña.
- Catálogo de productos con categorías y ATRIBUTOS DINÁMICOS (EAV/typed attributes).
- Carrito, checkout y creación de pedido.
- Pago mediante un sistema de PLUGINS desacoplado para poder añadir fácilmente nuevos métodos (p.ej., Stripe, Redsys, PayPal). Incluye un plugin “Dummy” para desarrollo.
- Entorno de desarrollo dockerizado con PostgreSQL y Mailpit para emails.
- Buenas prácticas (12-Factor, settings por entorno, pre-commit, linters, tests).

# Stack y versiones
- Python 3.12, Django 5.x, PostgreSQL 16.
- Django packages: django-allauth (auth por email), django-fsm (workflow de pedidos), django-environ, psycopg, django-debug-toolbar (dev), DRF (para endpoints JSON mínimos del checkout/pagos), whitenoise (static en prod).
- Calidad: ruff + black + isort + mypy (con configuración sensata).
- Tests: pytest + pytest-django + coverage.
- Front mínimo con Django templates + Tailwind CLI (o CDN si simplifica) para 4 pantallas básicas.

# Estructura del repo
- README.md (español) con instrucciones claras.
- Makefile con atajos: `make build up down logs shell test lint fmt migrate createsuperuser`.
- docker/
  - Dockerfile (multi-stage: builder + runtime, usuario no root)
  - entrypoint.sh (aplicar migrations, crear directorios, etc.)
- docker-compose.yml con servicios:
  - web (Django, puerto 8000)
  - db (Postgres 16, volumen persistente)
  - mailpit (web 8025, smtp 1025)
- .env.example y .env.dev con variables:
  - DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_SETTINGS_MODULE=config.settings.dev
  - DATABASE_URL=postgres://postgres:postgres@db:5432/app
  - EMAIL_HOST=mailpit, EMAIL_PORT=1025
  - ALLOWED_HOSTS=*, TIME_ZONE=Europe/Madrid, LANGUAGE_CODE=es-es
- config/
  - settings/{base.py,dev.py,prod.py}
  - urls.py, wsgi.py, asgi.py
- apps/
  - users/ (custom User con email como identificador)
  - catalog/ (Category, Product, atributos dinámicos)
  - cart/ (Cart, CartItem, sesión)
  - orders/ (Order, OrderItem, estados con django-fsm)
  - payments/ (infra de plugins + DummyProvider)
  - core/ (utilidades comunes)
- static/, templates/, scripts/…

# Requisitos funcionales
## Autenticación (users)
- Custom User con `email` único como USERNAME_FIELD (sin username).
- Registro con verificación de email (enviar email con enlace de activación vía Mailpit en dev).
- Login/Logout, reset de contraseña.
- Usa django-allauth configurado para email-only; vistas y templates básicos.

## Catálogo (catalog)
- Category (jerárquica simple) y Product con campos: name, slug, description, base_price (Decimal), currency (ISO), is_active.
- ATRIBUTOS DINÁMICOS tipados:
  - ProductAttribute (name, code, type in ["text","integer","decimal","boolean","date","enum"])
  - ProductAttributeOption (para “enum”)
  - ProductAttributeValue (product, attribute, y columnas de valor por tipo: value_text, value_int, value_decimal, value_bool, value_date, value_option)
- Admin para crear atributos y asignarlos a productos. Form amigable que muestre el input según el tipo.
- Filtros simples por categoría y por atributos (ej. color=rojo, talla=M).

	
- Cart session-based (no autenticado) movible a usuario tras login.
- CartItem con price snapshot y quantity.
- Checkout con captura de: email, shipping address, billing address (puede ser igual), aceptación de términos.
- Order + OrderItem; totales: subtotal, shipping (fijo o 0), taxes (stub), grand_total.
- State machine (django-fsm): draft → pending_payment → paid → canceled → refunded (solo transitions válidas).
- Un número de pedido legible (ej. AAA-YYYYMM-####).

## Pagos (payments) — PLUGINS
- Define una interfaz clara (abstract base class) `PaymentProvider`:
  - `code: str`, `display_name: str`
  - `start_payment(self, order, return_url: str, notify_url: str) -> PaymentInitResult`
    - Devuelve: `redirect_url` o datos para render.
  - `handle_webhook(self, request) -> PaymentWebhookResult`
  - `capture(self, order)`, `refund(self, order, amount)`
- Descubrimiento por settings: `PAYMENT_PROVIDERS = ["apps.payments.providers.dummy.DummyProvider"]`
  - Carga dinámica con importlib; registro en un registry singleton.
- Vista/endpoint:
  - `/checkout/payment/` elige provider.
  - `/payments/notify/<provider>/` para webhooks.
  - `/payments/return/<provider>/` para “success/cancel”.
- Implementa `DummyProvider` que “autoriza y captura” inmediatamente para dev, sin integraciones reales.
- Documenta cómo añadir un proveedor nuevo (ejemplo esqueleto para Stripe/Redsys con variables en settings).

## Vistas y URLs mínimas
- `/` home con listado simple de productos.
- `/catalog/` y `/catalog/<category-slug>/`
- `/product/<slug>/`
- `/cart/`, `POST /cart/add/<product_id>/`, `POST /cart/remove/<item_id>/`, `POST /cart/update/<item_id>/`
- `/checkout/` (datos envío/facturación) → `POST` crea `Order` en `pending_payment` → redirige a `/checkout/payment/`
- `/orders/<order_number>/` (detalle si es del usuario actual)
- Auth: `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/`, `/accounts/password/reset/` (allauth)

## APIs (DRF) mínimas (opcional pero útil)
- `GET /api/products/` con filtros por atributos, `GET /api/products/<id>/`
- `POST /api/cart/items/`, `PATCH /api/cart/items/<id>/`
- `POST /api/checkout/` → devuelve `payment.redirect_url` si aplica.
- `POST /api/payments/webhook/<provider>/` (CSRF exempt).

# Buenas prácticas y configuración
- Settings en `base.py` + `dev.py` + `prod.py`. Leer `.env` con django-environ.
- Logging estructurado a stdout. `DEBUG=True` solo en dev.
- Seguridad prod: `SECURE_*`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- Email en dev: SMTP a Mailpit (`EMAIL_HOST=mailpit`, `EMAIL_PORT=1025`).
- Archivos estáticos con WhiteNoise. `collectstatic` en build de imagen prod.
- Migraciones iniciales incluidas.
- Admin de Django configurado para todas las entidades clave con filtros de utilidad.

# Docker & ejecución
- `docker-compose up --build` deja todo corriendo en:
  - Web: http://localhost:8000
  - Mailpit UI: http://localhost:8025
- El entrypoint aplicará `migrate` y (si variable `DJANGO_CREATE_SUPERUSER=true`) creará un superuser con credenciales de `.env.dev`.

# Calidad y CI
- pre-commit con black, isort, ruff, mypy.
- `pytest -q` con cobertura mínima 85%. Tests para:
  - Registro y verificación de email.
  - Creación de producto y asignación de atributos dinámicos (incluye enum).
  - Flujo carrito → checkout → pedido → pago Dummy (estado pasa a paid).
  - Webhooks Dummy idempotentes.
- (Opcional) GitHub Actions workflow sencillo: lint + tests.

# Modelos (resumen)
- users.User(email, is_active, is_staff, date_joined, …).
- catalog.Category(parent, name, slug)
- catalog.Product(category, name, slug, description, base_price, currency, is_active, created_at, updated_at)
- catalog.ProductAttribute(name, code, type)
- catalog.ProductAttributeOption(attribute, value)
- catalog.ProductAttributeValue(product, attribute, value_text, value_int, value_decimal, value_bool, value_date, value_option)
- cart.Cart(session_key|user), cart.CartItem(cart, product, quantity, unit_price, total_price)
- orders.Order(user|email, number, status [FSM], billing_address, shipping_address, subtotal, tax_total, shipping_total, grand_total, created_at)
- orders.OrderItem(order, product, name_snapshot, unit_price, quantity, line_total)
- payments.Payment(order, provider_code, external_id, amount, currency, status, raw_response, created_at)
- payments.Transaction(payment, type [authorize|capture|refund|webhook], amount, raw, success, created_at)

# Plantillas mínimas
- Base con navbar (Home, Catalog, Cart, Login/Logout).
- Listado de productos (muestra atributos principales).
- Ficha de producto con tabla de atributos dinámicos y botón “Añadir al carrito”.
- Carrito con actualización de cantidades.
- Checkout (form direcciones) + selección de método de pago (Dummy por defecto).
- Pantallas Auth de allauth personalizadas lo justo.

# Comandos Makefile (implementa)
- `make build` (docker build), `make up`, `make down`, `make logs`, `make shell`, `make migrate`, `make createsuperuser`, `make test`, `make lint`, `make fmt`.

# Entregables
Entrega el código fuente completo listo para clonar y ejecutar, con:
1) README claro,
2) docker-compose.yml,
3) Dockerfile,
4) settings por entorno,
5) apps con modelos, admin, vistas, urls y forms/serializers necesarios,
6) sistema de pagos por plugins con DummyProvider funcional,
7) tests con cobertura,
8) pre-commit configurado.

Asegúrate de que, tras `docker-compose up --build`, pueda:
- Registrarme con email y ver el correo de verificación en Mailpit, activarme e iniciar sesión.
- Crear productos y atributos en el admin.
- Añadir al carrito, hacer checkout, elegir “Dummy” y completar el pago (pedido pasa a “paid”).
- Ver mi pedido en su URL de detalle.
- Crea un fichero PROMPT.md con toda la informacion del proyecto y los errores que salgan.
