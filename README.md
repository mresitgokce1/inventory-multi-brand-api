# Multi-Brand Inventory Management API

A Django REST API backend for managing multi-brand inventory systems with JWT authentication and role-based access control.

## Proje Özeti (Project Overview)

Bu proje, çoklu marka envanter yönetimi için Django REST Framework tabanlı bir backend API'sidir. Güvenli JWT kimlik doğrulaması, rol tabanlı yetkilendirme ve HttpOnly çerez desteği sunar.

This project is a Django REST Framework-based backend API for multi-brand inventory management. It provides secure JWT authentication, role-based authorization, and HttpOnly cookie support.

## Features

- **Custom User Model**: Email-based authentication instead of username
- **Multi-Brand Support**: Brands with auto-generated slugs
- **Role-Based Access**: ADMIN and BRAND_MANAGER roles
- **JWT Authentication**: Secure token-based authentication
- **HttpOnly Cookies**: Refresh tokens stored securely in HttpOnly cookies
- **API Documentation**: OpenAPI/Swagger schema endpoint
- **Modular Settings**: Separate configurations for development and production
- **Comprehensive Tests**: Full test coverage for authentication and models
- **Category & Product Management**: Full CRUD operations with brand isolation
- **Advanced Filtering**: Search, price range, category, and status filtering
- **Public API Endpoint**: Read-only access to active products
- **Image Processing**: Automatic image optimization and resizing

## Kurulum (Installation)

### Prerequisites
- Python 3.8+
- pip

### Setup Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd inventory-multi-brand-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run migrations:
```bash
export DJANGO_SETTINGS_MODULE=core_project.settings.dev
python manage.py migrate
```

6. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

7. Start the development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Category & Product Management Endpoints

#### GET/POST/PUT/DELETE `/api/categories/`
Manage product categories with brand-scoped access.

**Permissions:**
- Admins can access all categories
- Brand Managers can only access their brand's categories

**Filtering & Search:**
- `is_active=true/false` - Filter by active status
- `search=electronics` - Search by name

#### GET/POST/PUT/DELETE `/api/products/`
Manage products with full CRUD operations.

**Permissions:**
- Admins can access all products, must specify `brand` on creation
- Brand Managers can only access their brand's products, `brand` auto-assigned

**Filtering & Search:**
- `brand=1` - Filter by brand ID (admin only)
- `category=1` - Filter by category ID
- `is_active=true/false` - Filter by active status
- `min_price=10.00` - Minimum price filter
- `max_price=100.00` - Maximum price filter
- `search=laptop` - Search by name or SKU
- `ordering=price,-price,name,-name,created_at,-created_at,stock,-stock`

#### GET `/api/public/products/`
Public read-only endpoint for active products (no authentication required).

**Public Filtering & Search:**
- `brand=brand-slug` - Filter by brand slug
- `category=1` or `category=category-slug` - Filter by category ID or slug
- `min_price=10.00` - Minimum price filter
- `max_price=100.00` - Maximum price filter
- `search=laptop` - Search by name or SKU
- `ordering=price,-price,created_at,-created_at` - Sort options

### Authentication Endpoints

#### POST `/api/auth/login/`
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "BRAND_MANAGER",
    "brand_id": 1
  }
}
```

Sets HttpOnly refresh token cookie for token rotation.

#### POST `/api/auth/refresh/`
Refresh access token using HttpOnly cookie.

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST `/api/auth/logout/`
Logout and clear refresh token cookie.

**Response (200 OK):**
```json
{
  "detail": "Çıkış yapıldı."
}
```

### Schema Endpoint

#### GET `/api/schema/`
Returns OpenAPI 3.0 schema in YAML format.

## cURL Examples

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}' \
  -c cookies.txt
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -b cookies.txt
```

### Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -b cookies.txt
```

### Get API Schema
```bash
curl http://localhost:8000/api/schema/
```

## Product & Category API Examples

### Create a Category (Brand Manager)
```bash
curl -X POST http://localhost:8000/api/categories/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"name": "Electronics", "is_active": true}'
```

### Create a Product (Admin)
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN" \
  -d '{
    "name": "Smartphone",
    "sku": "PHONE001",
    "price": "599.99",
    "stock": 10,
    "brand": 1,
    "category": 1,
    "is_active": true
  }'
```

### Filter Products by Price Range
```bash
curl "http://localhost:8000/api/products/?min_price=100&max_price=1000&ordering=-price" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Search Products
```bash
curl "http://localhost:8000/api/products/?search=laptop" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Public Products (No Authentication)
```bash
# Get all active products
curl http://localhost:8000/api/public/products/

# Filter by brand
curl "http://localhost:8000/api/public/products/?brand=apple"

# Search and filter
curl "http://localhost:8000/api/public/products/?search=phone&min_price=200&max_price=800"
```

### Upload Product Image
```bash
curl -X PUT http://localhost:8000/api/products/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "image=@product-image.jpg" \
  -F "name=Updated Product Name"
```

## Models

### Brand
- `name`: Unique brand name
- `slug`: Auto-generated URL-friendly slug (can be manually overridden)
- `created_at`: Timestamp when brand was created

### User (Custom)
- `email`: Unique email address (used for login)
- `role`: Either "ADMIN" or "BRAND_MANAGER"
- `brand`: Foreign key to Brand (optional, SET_NULL on brand deletion)
- `password`: Hashed password
- Standard Django user fields: `is_active`, `is_staff`, `date_joined`, etc.

### Category
- `brand`: Foreign key to Brand (CASCADE)
- `name`: Category name (unique per brand)
- `slug`: Auto-generated slug (unique per brand)
- `is_active`: Boolean flag for active status
- `created_at` / `updated_at`: Timestamps

### Product
- `brand`: Foreign key to Brand (CASCADE)
- `category`: Foreign key to Category (SET_NULL, optional)
- `name`: Product name
- `slug`: Auto-generated slug (unique per brand)
- `sku`: Stock Keeping Unit (unique per brand)
- `description`: Product description (optional)
- `price`: Decimal price with 2 decimal places
- `stock`: Integer stock quantity
- `is_active`: Boolean flag for active status
- `image`: Original product image
- `image_small`: Auto-generated small image (400px width)
- `created_at` / `updated_at`: Timestamps

## Roles

- **ADMIN**: Full system access
- **BRAND_MANAGER**: Brand-specific access (associated with a specific brand)

## Image Processing

The system automatically processes uploaded product images:

- **Original Image**: Resized to maximum 1920px width while maintaining aspect ratio
- **Small Image**: Generated at 400px width for thumbnails/previews
- **Format**: All images converted to JPEG with 80% quality and progressive encoding
- **EXIF Removal**: Metadata automatically stripped for privacy
- **Naming**: Images named using product slug + hash for uniqueness
- **Storage**: Original images in `products/original/`, small images in `products/small/`

Images are processed automatically when a product is created or updated with an image file.

## Settings

The project uses modular settings:

- `core_project/settings/base.py`: Base configuration
- `core_project/settings/dev.py`: Development settings
- `core_project/settings/prod.py`: Production settings

Set `DJANGO_SETTINGS_MODULE` environment variable to switch between configurations:
```bash
export DJANGO_SETTINGS_MODULE=core_project.settings.dev
# or
export DJANGO_SETTINGS_MODULE=core_project.settings.prod
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
ADMIN_URL=your-admin-url-path/
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
CSRF_TRUSTED_ORIGINS=https://your-frontend-domain.com
```

## Testing

Run the test suite:

```bash
# Run all tests
export DJANGO_SETTINGS_MODULE=core_project.settings.dev
pytest

# Run specific test file
pytest accounts/tests/test_user_auth.py

# Run with verbose output
pytest -v
```

Test coverage includes:
- User authentication flow (login, refresh, logout)
- Brand slug auto-generation
- User model functionality
- Permission smoke tests

## Security Features

- **JWT Tokens**: Short-lived access tokens (10 minutes) with secure refresh mechanism
- **HttpOnly Cookies**: Refresh tokens stored in HttpOnly cookies to prevent XSS
- **Token Rotation**: Refresh tokens are rotated on each use
- **CORS Support**: Configurable CORS settings for frontend integration
- **Secure Cookies**: Automatic secure cookie settings in production

## Logging

Logs are written to both console and file (`logs/app.log`). Log levels can be configured per environment.

## License

MIT License - see LICENSE file for details.

## Development

This project follows Django best practices:
- Modular app structure
- Custom user model
- Comprehensive test coverage
- Environment-based configuration
- Secure authentication patterns

For production deployment, ensure:
1. Set `DEBUG=False`
2. Use a strong secret key
3. Configure proper ALLOWED_HOSTS
4. Set up HTTPS for secure cookies
5. Configure database for production use