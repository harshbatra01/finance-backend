# Finance Data Processing & Access Control Backend

A well-architected REST API backend for a finance dashboard system featuring role-based access control, financial records management, and dashboard analytics.

Built with **Python**, **Flask**, **SQLAlchemy**, and **SQLite**.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
  - [Authentication](#authentication)
  - [User Management](#user-management)
  - [Financial Records](#financial-records)
  - [Dashboard Analytics](#dashboard-analytics)
- [Role-Based Access Control](#role-based-access-control)
- [Error Handling](#error-handling)
- [Validation Rules](#validation-rules)
- [Design Decisions & Tradeoffs](#design-decisions--tradeoffs)
- [Assumptions](#assumptions)
- [Testing](#testing)

---

## Architecture Overview

The application follows a **layered architecture** with clear separation of concerns:

```
┌──────────────────────────────────────────────────────┐
│                   HTTP Request                        │
├──────────────────────────────────────────────────────┤
│  Middleware Layer                                      │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ JWT Auth    │→ │ RBAC     │→ │ Error Handler    │ │
│  │ (Decorator) │  │ (Roles)  │  │ (Global)         │ │
│  └─────────────┘  └──────────┘  └──────────────────┘ │
├──────────────────────────────────────────────────────┤
│  Route Layer (Blueprints)                             │
│  Thin handlers — parse input, call service, format    │
│  response. No business logic here.                    │
├──────────────────────────────────────────────────────┤
│  Service Layer (Business Logic)                       │
│  Enforces business rules, orchestrates data access,   │
│  handles validation beyond field-level checks.        │
├──────────────────────────────────────────────────────┤
│  Schema Layer (Marshmallow)                           │
│  Input validation, serialization/deserialization.     │
├──────────────────────────────────────────────────────┤
│  Model Layer (SQLAlchemy ORM)                         │
│  Database models, relationships, data serialization.  │
├──────────────────────────────────────────────────────┤
│  SQLite Database                                      │
└──────────────────────────────────────────────────────┘
```

**Key Design Principles:**
- **Separation of Concerns**: Routes handle HTTP, services handle business logic, models handle data.
- **Decorator-based Auth/RBAC**: Clean, declarative, and visible at the endpoint level.
- **Consistent API Responses**: Every response follows the same JSON structure.
- **Factory Pattern**: The app uses Flask's application factory for testability and flexibility.

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Language | Python 3.9 | Clean syntax, strong ecosystem for backend development |
| Framework | Flask 2.3 | Lightweight, explicit, allows full architectural control |
| ORM | SQLAlchemy 2.0 | Industry-standard, powerful query building, great for analytics aggregations |
| Database | SQLite | Relational database with zero configuration — easily swappable to PostgreSQL |
| Validation | Marshmallow 3.20 | Schema-based validation with clear error messages |
| Authentication | PyJWT 2.8 | Stateless JWT token-based authentication |
| Password Hashing | Werkzeug | Secure PBKDF2 password hashing (built into Flask's dependency) |
| CORS | Flask-CORS | Cross-origin support for frontend integration |
| API Docs | Flasgger | Auto-generated Swagger/OpenAPI documentation |

---

## Project Structure

```
finance-backend/
├── config.py                    # Environment-based configuration
├── run.py                       # Application entry point
├── seed.py                      # Database seeding script
├── requirements.txt             # Pinned dependencies
├── .env.example                 # Environment variable template
├── test_api.sh                  # API test suite (47 tests)
│
├── app/
│   ├── __init__.py              # Application factory (create_app)
│   ├── extensions.py            # Flask extensions (SQLAlchemy)
│   │
│   ├── models/                  # Database models
│   │   ├── user.py              # User model with password hashing
│   │   └── record.py            # FinancialRecord model
│   │
│   ├── schemas/                 # Input validation schemas
│   │   ├── user.py              # User registration, update, login schemas
│   │   └── record.py            # Record create, update schemas
│   │
│   ├── services/                # Business logic layer
│   │   ├── user_service.py      # User CRUD, authentication, JWT
│   │   ├── record_service.py    # Record CRUD, filtering, pagination
│   │   └── dashboard_service.py # Aggregations, trends, analytics
│   │
│   ├── routes/                  # API route blueprints
│   │   ├── auth_routes.py       # /api/auth/* endpoints
│   │   ├── user_routes.py       # /api/users/* endpoints
│   │   ├── record_routes.py     # /api/records/* endpoints
│   │   └── dashboard_routes.py  # /api/dashboard/* endpoints
│   │
│   ├── middleware/              # Cross-cutting concerns
│   │   ├── auth.py              # JWT authentication decorator
│   │   ├── rbac.py              # Role-based access control decorator
│   │   └── error_handler.py     # Global error handling
│   │
│   └── utils/                   # Shared utilities
│       ├── exceptions.py        # Custom exception hierarchy
│       └── responses.py         # Standardized response helpers
```

---

## Setup & Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd finance-backend

# 2. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and set a secure SECRET_KEY for production

# 5. Seed the database with sample data
python seed.py

# 6. Start the development server
python run.py
```

The server will start at **http://localhost:5050** by default.

### Render (No Shell) Seeding

On Render's free tier, one-off shells may be unavailable. This project supports
an optional, safe auto-seed mode for demo deployments:

- Set `AUTO_SEED=true` in your Render web service environment variables.
- Deploy once; the app will seed **only if** the database has no users.

Seeded demo credentials:
- `admin@example.com` / `password123`
- `analyst@example.com` / `password123`
- `viewer@example.com` / `password123`

### Seed Data

The `seed.py` script creates:
- **3 users** (one per role):
  - `admin@example.com` / `password123` (Admin)
  - `analyst@example.com` / `password123` (Analyst)
  - `viewer@example.com` / `password123` (Viewer)
- **35 financial records** spanning 6 months with realistic income and expense entries

---

## Database Schema

### Users Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String(36) | PK, UUID | Unique identifier |
| email | String(255) | Unique, Not Null, Indexed | Login email |
| name | String(100) | Not Null | Display name |
| password_hash | String(256) | Not Null | PBKDF2 salted hash |
| role | String(20) | Not Null, Default: 'viewer' | viewer \| analyst \| admin |
| status | String(20) | Not Null, Default: 'active' | active \| inactive |
| created_at | DateTime | Not Null | Account creation timestamp (UTC) |
| updated_at | DateTime | Not Null | Last update timestamp (UTC) |

### Financial Records Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String(36) | PK, UUID | Unique identifier |
| amount | Numeric(12,2) | Not Null | Transaction amount (always positive) |
| type | String(20) | Not Null | income \| expense |
| category | String(100) | Not Null, Indexed | Transaction category |
| date | Date | Not Null, Indexed | Transaction date |
| description | String(500) | Nullable | Optional notes |
| created_by | String(36) | FK → users.id, Indexed | Creator reference |
| created_at | DateTime | Not Null | Record creation timestamp (UTC) |
| updated_at | DateTime | Not Null | Last update timestamp (UTC) |

### Relationships
- **User → FinancialRecord**: One-to-Many (a user can create many records)
- **Cascade Delete**: Deleting a user removes their associated records

---

## API Reference

### Base URL
```
http://localhost:5050/api
```

### Response Format

All responses follow a consistent format:

**Success:**
```json
{
    "success": true,
    "data": { ... },
    "message": "Human-readable message"
}
```

**Error:**
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "details": { ... }
    }
}
```

---

### Authentication

#### `POST /api/auth/register`
Create a new user account.

**Request Body:**
```json
{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "securepass123",
    "role": "viewer"
}
```

**Response (201):**
```json
{
    "success": true,
    "data": {
        "id": "uuid",
        "email": "user@example.com",
        "name": "John Doe",
        "role": "viewer",
        "status": "active",
        "created_at": "2026-04-06T12:00:00.000000Z",
        "updated_at": "2026-04-06T12:00:00.000000Z"
    },
    "message": "User registered successfully"
}
```

#### `POST /api/auth/login`
Authenticate and receive a JWT token.

**Request Body:**
```json
{
    "email": "admin@example.com",
    "password": "password123"
}
```

**Response (200):**
```json
{
    "success": true,
    "data": {
        "token": "eyJhbGciOi...",
        "user": { ... }
    },
    "message": "Login successful"
}
```

#### `GET /api/auth/me`
Get the current authenticated user's profile. Requires Bearer token.

---

### User Management

> All user management endpoints require **Admin** role.

#### `GET /api/users`
List all users. Optional query params: `role`, `status`.

#### `GET /api/users/:id`
Get a specific user by ID.

#### `PUT /api/users/:id`
Update user profile (email, name, password).

#### `PATCH /api/users/:id/role`
Change a user's role.

**Request Body:**
```json
{ "role": "analyst" }
```

#### `PATCH /api/users/:id/status`
Activate or deactivate a user.

**Request Body:**
```json
{ "status": "inactive" }
```

#### `DELETE /api/users/:id`
Permanently delete a user and their records.

---

### Financial Records

#### `POST /api/records` _(Admin only)_
Create a new financial record.

**Request Body:**
```json
{
    "amount": 5000.00,
    "type": "income",
    "category": "Salary",
    "date": "2026-03-15",
    "description": "March salary payment"
}
```

#### `GET /api/records` _(All authenticated users)_
List records with filtering, sorting, and pagination.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by `income` or `expense` |
| `category` | string | Filter by category (case-insensitive partial match) |
| `date_from` | date | Records on or after this date (YYYY-MM-DD) |
| `date_to` | date | Records on or before this date (YYYY-MM-DD) |
| `min_amount` | number | Records with amount ≥ this value |
| `max_amount` | number | Records with amount ≤ this value |
| `sort_by` | string | Sort field: `date`, `amount`, `category`, `type`, `created_at` |
| `sort_order` | string | `asc` or `desc` (default: `desc`) |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Records per page (default: 20, max: 100) |

**Example:**
```
GET /api/records?type=expense&category=rent&sort_by=amount&sort_order=desc&page=1&per_page=10
```

#### `GET /api/records/:id` _(All authenticated users)_
Get a specific record.

#### `PUT /api/records/:id` _(Admin only)_
Update a record. Only provided fields are modified.

#### `DELETE /api/records/:id` _(Admin only)_
Delete a record.

---

### Dashboard Analytics

> Dashboard endpoints are accessible to all authenticated roles (**Viewer**, **Analyst**, **Admin**).

#### `GET /api/dashboard/summary`
Overall financial summary.

**Response:**
```json
{
    "data": {
        "total_income": 35620.00,
        "total_expenses": 12858.99,
        "net_balance": 22761.01,
        "total_records": 35
    }
}
```

#### `GET /api/dashboard/category-breakdown`
Income and expense totals grouped by category.

**Response:**
```json
{
    "data": [
        {
            "category": "Salary",
            "total_income": 30200.00,
            "total_expenses": 0.00,
            "net_amount": 30200.00,
            "record_count": 6
        }
    ]
}
```

#### `GET /api/dashboard/trends`
Monthly income/expense trends. Query param: `months` (default: 12, max: 24).

**Response:**
```json
{
    "data": [
        {
            "year": 2026,
            "month": 1,
            "month_label": "Jan 2026",
            "total_income": 5000.00,
            "total_expenses": 2500.00,
            "net_amount": 2500.00
        }
    ]
}
```

#### `GET /api/dashboard/recent-activity`
Most recent records. Query param: `limit` (default: 10, max: 50).

---

## Role-Based Access Control

### Roles

| Role | Description |
|------|-------------|
| **Viewer** | Can only view dashboard analytics |
| **Analyst** | Can view records and access dashboard analytics |
| **Admin** | Full access — manage records, users, and view analytics |

### Permission Matrix

| Action | Viewer | Analyst | Admin |
|--------|--------|---------|-------|
| View records | ❌ | ✅ | ✅ |
| Filter/sort records | ❌ | ✅ | ✅ |
| Create records | ❌ | ❌ | ✅ |
| Update records | ❌ | ❌ | ✅ |
| Delete records | ❌ | ❌ | ✅ |
| Dashboard summary | ✅ | ✅ | ✅ |
| Category breakdown | ✅ | ✅ | ✅ |
| Monthly trends | ✅ | ✅ | ✅ |
| Recent activity | ✅ | ✅ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

### Implementation

RBAC is implemented using composable **Python decorators**:

```python
@app.route('/api/records', methods=['POST'])
@require_auth                        # Step 1: Validate JWT token
@require_role('admin')               # Step 2: Check user's role
def create_record():
    ...
```

This approach keeps authorization rules **visible and co-located** with the endpoints they protect.

### Business Rules
- **Last Admin Protection**: The system prevents removing, deactivating, or demoting the last active admin to avoid system lockout.
- **Inactive User Rejection**: Inactive users cannot authenticate even with valid credentials.

---

## Error Handling

### Custom Exception Hierarchy

```
AppException (500)
├── ValidationError (400)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── NotFoundError (404)
└── ConflictError (409)
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Successful GET, PUT, PATCH |
| 201 | Resource created (POST) |
| 204 | Resource deleted (DELETE) |
| 400 | Validation errors, bad input |
| 401 | Missing/invalid token, wrong credentials |
| 403 | Insufficient role permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate email) |
| 500 | Unexpected server errors |

### Error Response Examples

**Validation Error (400):**
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "amount": ["Must be a positive number"],
            "type": ["Must be one of: income, expense"]
        }
    }
}
```

**Authorization Error (403):**
```json
{
    "success": false,
    "error": {
        "code": "AUTHORIZATION_ERROR",
        "message": "This action requires one of the following roles: admin. Your role: viewer."
    }
}
```

---

## Validation Rules

### User Registration
- **email**: Required, valid email format, unique in system
- **name**: Required, 2–100 characters, cannot be blank
- **password**: Required, 8–128 characters
- **role**: Optional, must be `viewer`, `analyst`, or `admin` (defaults to `viewer`)

### Financial Record
- **amount**: Required, must be a positive number, max 2 decimal places
- **type**: Required, must be `income` or `expense`
- **category**: Required, 1–100 characters, cannot be blank
- **date**: Required, ISO format (YYYY-MM-DD), cannot be in the future
- **description**: Optional, max 500 characters

### Query Parameter Validation
- **type filter**: Must be `income` or `expense`
- **sort_by**: Must be one of: `date`, `amount`, `category`, `type`, `created_at`
- **sort_order**: Must be `asc` or `desc`
- **min/max_amount**: Must be valid numbers
- **page/per_page**: Clamped to valid ranges (per_page max: 100)

---

## Design Decisions & Tradeoffs

### 1. SQLite Over PostgreSQL
SQLite was chosen for zero-configuration setup. The application uses SQLAlchemy ORM throughout, so switching to PostgreSQL requires only changing the `DATABASE_URL` environment variable — no code changes needed.

### 2. Modular Blueprints Over Single Router
Each API domain (auth, users, records, dashboard) has its own Flask Blueprint. This makes the codebase navigable — you can find all record-related code in `routes/record_routes.py` and `services/record_service.py`.

### 3. Service Layer Pattern
Business logic lives in the service layer, not in route handlers. This means:
- Route handlers stay thin (parse input → call service → format output)
- Business rules are testable without HTTP overhead
- Logic can be reused across different routes if needed

### 4. Decorator-Based Auth/RBAC
Authentication and authorization are applied as decorators, making permissions visible at the route definition level. This is more explicit than middleware-based approaches where authorization rules may be distant from the routes they protect.

### 5. SQL-Level Aggregations for Dashboard
Dashboard analytics use SQLAlchemy's `func` module for database-level computation (SUM, COUNT, GROUP BY) rather than loading all records into Python. This is crucial for performance as data grows.

### 6. UUID Primary Keys
UUIDs prevent sequential ID enumeration attacks and are better suited for distributed systems. The tradeoff is slightly larger storage and less human-readable IDs.

### 7. Consistent Response Format
Every API response (success or error) follows the same JSON structure. This makes the API predictable for frontend consumers — they always know where to find the data and error details.

### 8. Password Security
Passwords are hashed using Werkzeug's PBKDF2 implementation with individual salts. Plain-text passwords are never stored or logged.

---

## Assumptions

1. **Single-tenant system**: All users operate within the same organization/dashboard.
2. **Admin bootstrapping**: The seed script creates the initial admin. In production, this would be handled via a setup CLI command or migration.
3. **Record ownership**: All records are visible to all authenticated users (no per-user data isolation). The `created_by` field serves as an audit trail.
4. **Monetary precision**: Amounts use `Numeric(12,2)` which supports values up to 9,999,999,999.99 — sufficient for most business applications.
5. **UTC timestamps**: All timestamps are stored in UTC. Timezone conversion is expected to happen on the client side.
6. **Token-based sessions**: JWTs are stateless — there's no server-side session store. Token revocation would require additional infrastructure (e.g., a blocklist).

---

## Testing

### Automated Test Suite

The project includes both endpoint and Python unit tests:

```bash
# Start the server first
python run.py

# In another terminal, run tests
bash test_api.sh

# Run service-layer unit tests
pytest -q
```

**Test Coverage (47 tests):**
- 🔐 **Authentication**: Login, registration, profile, token validation
- 👥 **User Management**: CRUD, role changes, status changes, deletion
- 💰 **Financial Records**: CRUD, filtering, sorting, pagination
- 📊 **Dashboard**: Summary, category breakdown, trends, recent activity
- 🛡️ **Validation**: Missing fields, invalid data, boundary conditions
- 🔒 **RBAC**: Role enforcement across all endpoints (viewer/analyst/admin)
- ⚠️ **Error Handling**: 400, 401, 403, 404, 409 responses

### Health Check

```bash
curl http://localhost:5050/api/health
# {"service": "finance-backend", "status": "healthy"}
```

---

## Future Enhancements

The architecture is designed to easily support:
- **Search** — The category filter already supports partial matching; full-text search can be added
- **Redis-backed rate limiting** — Switch `RATELIMIT_STORAGE_URI` from in-memory to Redis for distributed deployments
- **OpenAPI enrichment** — Add per-route response schema examples for richer `/api/docs` exploration
- **Background jobs** — Move heavy analytics to scheduled tasks as the dataset grows

## Operational Security Defaults

- **Soft delete enforcement**: `deleted_at` is used for users and records, and all read/auth paths exclude deleted entities.
- **Payload size limit**: `MAX_CONTENT_LENGTH` (default `1MB`) rejects oversized request bodies globally.
- **Rate limiting**: Flask-Limiter is enabled globally with endpoint-specific limits on auth and mutating record routes.

## API Docs

- Swagger UI is available at `GET /api/docs`
- OpenAPI spec is available at `GET /apispec.json`

## Docker

```bash
docker build -t finance-backend .
docker run --rm -p 5000:5000 --env-file .env finance-backend
```

---

## License

This project was built as a backend assessment submission.
