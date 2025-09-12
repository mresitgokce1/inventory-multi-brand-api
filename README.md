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

### Catalog Endpoints

#### GET `/api/categories/`
List categories accessible to the authenticated user.
- **Admin users**: See all categories across all brands
- **Brand managers**: See only categories from their own brand

#### POST `/api/categories/`
Create a new category.
- **Admin users**: Can specify any brand
- **Brand managers**: Category automatically assigned to their brand

#### GET `/api/categories/{id}/`
Retrieve a specific category (if user has access).

#### PUT `/api/categories/{id}/`
Update a specific category (if user has access).

#### DELETE `/api/categories/{id}/`
Delete a specific category (if user has access).

#### GET `/api/products/`
List products accessible to the authenticated user.
- **Admin users**: See all products across all brands
- **Brand managers**: See only products from their own brand

#### POST `/api/products/`
Create a new product.
- **Admin users**: Can specify any brand
- **Brand managers**: Product automatically assigned to their brand
- **Validations**: price >= 0, stock >= 0

#### GET `/api/products/{id}/`
Retrieve a specific product (if user has access).

#### PUT `/api/products/{id}/`
Update a specific product (if user has access).

#### DELETE `/api/products/{id}/`
Delete a specific product (if user has access).

### Filtering, Search, and Ordering

#### Product Filtering, Search, and Ordering

**Filtering:**
- `category` - Filter by category ID: `?category=1`
- `is_active` - Filter by active status: `?is_active=true`
- `min_price` - Filter by minimum price: `?min_price=10.00`
- `max_price` - Filter by maximum price: `?max_price=100.00`
- `brand` - Filter by brand ID (admin only): `?brand=2`

**Search:**
- Search in name and SKU: `?search=laptop`

**Ordering:**
- Order by name: `?ordering=name` (ascending) or `?ordering=-name` (descending)
- Order by price: `?ordering=price` or `?ordering=-price`
- Order by creation date: `?ordering=created_at` or `?ordering=-created_at` (default)
- Order by stock: `?ordering=stock` or `?ordering=-stock`

**Combined examples:**
```
GET /api/products/?category=1&is_active=true&min_price=50&max_price=200&search=gaming&ordering=-price
GET /api/products/?is_active=true&ordering=name
GET /api/products/?brand=2&min_price=100&ordering=-created_at  # Admin only
```

#### Category Filtering, Search, and Ordering

**Filtering:**
- `is_active` - Filter by active status: `?is_active=true`
- `name` - Filter by name (case-insensitive contains): `?name=electronics`

**Search:**
- Search in name: `?search=gaming`

**Ordering:**
- Order by name: `?ordering=name` (default, ascending) or `?ordering=-name` (descending)
- Order by creation date: `?ordering=created_at` or `?ordering=-created_at`

**Combined examples:**
```
GET /api/categories/?is_active=true&search=electronics&ordering=name
GET /api/categories/?name=tech&ordering=-created_at
```

## Public API Endpoints

### Public Products Endpoint

#### GET `/api/public/products/`
Browse active products without authentication. Public read-only access to product catalog.

**Features:**
- **No authentication required** - AllowAny permission
- **Only active products** - Inactive products are excluded
- **Public filtering** - Limited filtering options for public use
- **Search** - Search by product name and SKU
- **Ordering** - Sort results by price or creation date

**Public filters:**
- `brand` - Filter by brand slug: `?brand=techcorp`
- `category` - Filter by category ID or slug: `?category=1` or `?category=laptops`
- `min_price` - Filter by minimum price: `?min_price=50.00`
- `max_price` - Filter by maximum price: `?max_price=500.00`

**Search:**
- Search in product name and SKU: `?search=gaming`

**Ordering:**
- Order by price: `?ordering=price` (ascending) or `?ordering=-price` (descending)
- Order by creation date: `?ordering=created_at` or `?ordering=-created_at` (default)

**Response fields:**
- `id` - Product ID
- `name` - Product name
- `slug` - Product slug
- `price` - Product price
- `image_small` - Small product image URL (if available)
- `brand` - Brand information (`id`, `name`, `slug`)
- `category` - Category information (`id`, `name`, `slug`)

**Example Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Gaming Laptop",
      "slug": "gaming-laptop",
      "price": "1299.99",
      "image_small": null,
      "brand": {
        "id": 1,
        "name": "TechCorp",
        "slug": "techcorp"
      },
      "category": {
        "id": 1,
        "name": "Laptops",
        "slug": "laptops"
      }
    }
  ]
}
```

**Public API Examples:**

```bash
# Get all active products
curl http://localhost:8000/api/public/products/

# Filter by brand slug
curl "http://localhost:8000/api/public/products/?brand=techcorp"

# Filter by category ID
curl "http://localhost:8000/api/public/products/?category=1"

# Filter by category slug
curl "http://localhost:8000/api/public/products/?category=laptops"

# Filter by price range
curl "http://localhost:8000/api/public/products/?min_price=100&max_price=1000"

# Search products
curl "http://localhost:8000/api/public/products/?search=gaming"

# Order by price (ascending)
curl "http://localhost:8000/api/public/products/?ordering=price"

# Order by price (descending)
curl "http://localhost:8000/api/public/products/?ordering=-price"

# Order by creation date (newest first, default)
curl "http://localhost:8000/api/public/products/?ordering=-created_at"

# Combined filters
curl "http://localhost:8000/api/public/products/?brand=techcorp&min_price=500&ordering=-price"
curl "http://localhost:8000/api/public/products/?category=laptops&search=gaming&max_price=2000"
```

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

## Image Processing Pipeline

### Overview
Product images are automatically processed when uploaded to optimize storage and improve loading performance:

- **Original Image Processing**: Images are normalized to ensure consistent quality and format
- **Small Variant Generation**: A smaller thumbnail version is automatically created for listings and previews
- **Graceful Error Handling**: Image processing failures don't prevent product creation/updates

### Processing Specifications

#### Normalized Original Image
- **Maximum Width**: 1920 pixels (maintains aspect ratio)
- **Format**: RGB JPEG at 80% quality
- **EXIF Data**: Stripped for privacy and smaller file size
- **Optimization**: Images are optimized for web delivery

#### Small Variant Image (Thumbnail)
- **Width**: 400 pixels (maintains aspect ratio)
- **Format**: RGB JPEG at 80% quality  
- **EXIF Data**: Stripped for privacy and smaller file size
- **Use Case**: Product listings, previews, and mobile views

### File Size Assumptions
- **Large products images** (original): Typically 50KB - 500KB after processing
- **Small variant images**: Typically 5KB - 50KB after processing
- **Supported input formats**: JPEG, PNG, WebP, and other PIL-supported formats
- **Output format**: Always JPEG for consistency and optimal compression

### Automatic Processing
Images are processed automatically via Django signals when:
- A new product is created with an image
- An existing product's image is updated
- A product has an image but missing small variant

Processing happens asynchronously after the product is saved, ensuring:
- No delays in API responses
- Graceful fallback if processing fails
- Comprehensive error logging for troubleshooting

### Storage Structure
```
media/
├── products/              # Original uploaded images
│   ├── image1.jpg
│   └── image2_processed.jpg
└── products/small/        # Auto-generated small variants
    ├── image1_small.jpg
    └── image2_processed_small.jpg
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
- `brand`: Foreign key to Brand (CASCADE on brand deletion)
- `name`: Category name (unique per brand)
- `slug`: Auto-generated URL-friendly slug (unique per brand, with collision handling)
- `is_active`: Boolean flag for active categories
- `created_at`, `updated_at`: Timestamp fields

### Product
- `brand`: Foreign key to Brand (CASCADE on brand deletion)
- `category`: Foreign key to Category (optional, SET_NULL on category deletion)
- `name`: Product name
- `slug`: Auto-generated URL-friendly slug (unique per brand, with collision handling)
- `sku`: Stock Keeping Unit (unique per brand)
- `description`: Product description (optional)
- `price`: Product price (Decimal with 10 digits, 2 decimal places)
- `stock`: Inventory count (default: 0)
- `is_active`: Boolean flag for active products
- `image`, `image_small`: Optional image fields
- `created_at`, `updated_at`: Timestamp fields

## Roles

- **ADMIN**: Full system access
- **BRAND_MANAGER**: Brand-specific access (associated with a specific brand)

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

## Catalog Module Rollout

The catalog functionality is being implemented in phases:

- **Phase 1: Models foundation** - Core Category and Product models with brand-scoped uniqueness (✓ Complete)
- **Phase 2: CRUD serializers & viewsets** - Brand scoping permissions and API endpoints (✓ Complete)
- **Phase 3: Filtering, search, ordering** - Advanced query capabilities (✓ Complete)
- **Phase 4: Public read-only products endpoint** - Public API for product browsing (✓ Complete)
- **Phase 5: Image processing + small variant** - Automatic image resizing and optimization (✓ Complete)
- **Phase 6: Tests + OpenAPI + doc polish** - Comprehensive testing, API documentation, and final polish