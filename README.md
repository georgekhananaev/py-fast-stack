# PyFastStack v1.0.0

Modern, production-ready Python web stack built with FastAPI, Tailwind CSS, and HTMX. Lightning-fast async architecture with JWT auth, real-time UI updates, and beautiful dark mode.

## 🚀 Features

### Core Tech Stack
- **FastAPI** - Lightning-fast async Python web framework
- **Tailwind CSS** - Modern utility-first CSS for beautiful UIs
- **HTMX** - Dynamic pages without writing JavaScript
- **Jinja2** - Fast and designer-friendly templating

### Developer Experience
- **100% Type Hints** - Full type safety with Pydantic validation
- **Async Everything** - Database, auth, even password hashing runs async
- **Auto API Docs** - Interactive Swagger UI out of the box
- **Hot Reload** - See changes instantly in development

### Production Ready
- **JWT Authentication** - Secure token-based auth system
- **Async SQLAlchemy 2.0** - Modern ORM with connection pooling
- **Gunicorn + Uvicorn** - Production-grade ASGI server setup
- **Dark/Light Mode** - Beautiful theme switching with CSS transitions
- **Rate Limiting** - Protection against brute force attacks

### Performance
- **10,000+ concurrent connections** - Handle serious traffic
- **Request streaming** - Support for large file uploads (100MB+)
- **GZip compression** - Automatic response compression
- **Connection pooling** - Optimized database performance

## 🏗️ Project Structure

```
pyfaststack/
├── app/
│   ├── api/            # API endpoints and dependencies
│   ├── core/           # Core configuration and security
│   ├── crud/           # Database CRUD operations
│   ├── db/             # Database configuration
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── utils/          # Utility functions
│   └── web/            # Web routes for UI
├── static/             # Static files (CSS, JS, images)
├── templates/          # Jinja2 HTML templates
├── tests/              # Test suite with performance benchmarks
├── pyproject.toml      # Project configuration and dependencies
├── gunicorn.conf.py    # Gunicorn server configuration
└── run.py              # Application entry point
```

## 📋 Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (Fast Python package installer)

## 🛠️ Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Or on macOS: brew install uv
   # Or with pip: pip install uv
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/georgekhananaev/py-fast-stack.git
   cd pyfaststack
   ```

3. **Install dependencies with uv**
   ```bash
   uv sync
   ```
   
   This will:
   - Create a virtual environment automatically
   - Install all dependencies from pyproject.toml
   - Use Python 3.13 as specified

4. **Set up environment variables**
   ```bash
   # Create a .env file (optional, has defaults)
   cp .env.example .env
   ```
   
   Update `.env` with your settings:
   - `SECRET_KEY`: Generate a secure secret key for production
   - `DATABASE_URL`: Database connection string (SQLite by default)

## 🚀 Running the Application

### Development Mode
```bash
uv run python run.py
# Or with auto-reload:
uv run uvicorn app.main:app --reload
```

On first run, the application will:
- Initialize the database automatically
- Create a root superuser with generated credentials
- Display credentials in colored output in the terminal

The application will be available at:
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Production Mode
For production, set DEBUG=False in .env and run:
```bash
uv run python run.py
# Or directly with Gunicorn:
uv run gunicorn app.main:app -c gunicorn.conf.py
```

This uses Gunicorn with Uvicorn workers for optimal performance.

## 🔧 Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```env
# Optional .env configuration
DATABASE_URL=sqlite+aiosqlite:///./pyfaststack.db
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_NAME=PyFastStack
APP_VERSION=1.0.0
DEBUG=True
```

### Database
By default, PyFastStack uses SQLite with optimized async operations. For production, PostgreSQL is recommended:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

Database features:
- Connection pooling (AsyncAdaptedQueuePool for PostgreSQL)
- Connection health checks (pool_pre_ping)
- Automatic connection recycling
- Indexed fields for optimal query performance

## 🔒 Security Features

### Authentication & Authorization
- **Password Hashing** - Bcrypt with salt for secure password storage
- **JWT Tokens** - Secure authentication tokens with expiration
- **Role-Based Access** - Superuser and regular user roles
- **Async Password Operations** - Non-blocking password hashing and verification

### Rate Limiting
- **Login Protection** - 5 attempts per minute per IP
- **Registration Protection** - 3 new accounts per minute per IP
- **Password Change Protection** - 3 attempts per minute
- **Newsletter Subscription** - 3 subscriptions per minute
- **Health Endpoint** - No rate limiting (for monitoring)

### Security Headers & Middleware
- **CORS Protection** - Configurable allowed origins
- **Trusted Host Middleware** - Prevents host header attacks
- **Security Headers** - X-Content-Type-Options, X-Frame-Options, etc.
- **Request Size Limits** - 100MB max request size
- **SQL Injection Protection** - Via SQLAlchemy ORM
- **Type Validation** - Pydantic validates all input data

### Additional Security
- **HTTPS Ready** - Secure cookie settings for production
- **Environment Variables** - Sensitive data kept out of code
- **Protected Routes** - Automatic authentication checks
- **User Deletion Protection** - Root user cannot be deleted

## 🎨 UI Features

### Dark/Light Mode
- Click the sun/moon icon in the navigation bar
- Theme preference is saved in localStorage
- Smooth transitions between themes

### Responsive Design
- Mobile-first approach with Tailwind CSS
- Adapts to all screen sizes
- Touch-friendly interface

## 📚 API Endpoints

### Health Check
- `GET /health` - Health check endpoint (no rate limiting)
  - Returns: `{"status": "healthy", "datetime": "2024-01-20T10:30:00", "timestamp": 1705749000.0}`
  - Optimized for monitoring and benchmarking

### Authentication
- `POST /api/v1/auth/register` - Register new user (rate limited: 3/min)
- `POST /api/v1/auth/login` - Login (rate limited: 5/min)
- `GET /api/v1/auth/me` - Get current user info

### Users (requires authentication)
- `GET /api/v1/users/` - List users (admin only)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user (admin only)

### Newsletter
- `POST /api/v1/subscribe` - Subscribe to newsletter (rate limited: 3/min)
- `DELETE /api/v1/unsubscribe/{email}` - Unsubscribe
- `GET /api/v1/subscriptions` - List subscribers (admin only)

## 🧪 Testing

PyFastStack includes comprehensive tests for authentication, user management, performance, and security features.

### Running Tests

1. **Start the server** (tests require a running server):
   ```bash
   uv run uvicorn app.main:app --reload
   ```

2. **Create test users** (one-time setup):
   ```bash
   uv run python tests/create_test_users.py
   ```

3. **Run all tests**:
   ```bash
   # Using the test runner (recommended)
   uv run python run_tests.py
   
   # Or with pytest directly
   uv run pytest
   
   # Run with coverage
   uv run pytest --cov=app --cov-report=html
   
   # Run specific test categories
   uv run pytest -m "not rate_limit"  # Skip rate limit tests
   uv run pytest tests/test_auth.py    # Run only auth tests
   ```

### Test Categories

1. **Authentication Tests** (`test_auth.py`)
   - User registration with validation
   - Login with various scenarios
   - JWT token validation
   - Password security

2. **User Management Tests** (`test_users.py`)
   - CRUD operations with permissions
   - Profile management
   - Superuser capabilities

3. **Web UI Tests** (`test_users_web.py`)
   - Form submissions
   - Cookie-based authentication
   - User dashboard functionality

4. **Performance Tests** (`test_performance.py`)
   - Response time benchmarks
   - Concurrent request handling
   - Database operation performance
   - Load testing scenarios

5. **Rate Limiter Tests** (`test_rate_limiter.py`)
   - Login rate limiting
   - Registration rate limiting
   - API endpoint protection
   - Rate limit reset behavior

### Performance Benchmarks

Run performance tests to see detailed metrics:
```bash
uv run pytest tests/test_performance.py -v -s
```

Expected performance on typical hardware:
- **Health endpoint**: 100-500+ requests/second
- **Authenticated endpoints**: 50-200 requests/second
- **Database operations**: 20-100 requests/second
- **Response times**: <50ms for health, <200ms for auth endpoints

## 🧹 Code Quality

```bash
# Format code with Black
uv run black .

# Lint with Ruff
uv run ruff check .

# Type check with MyPy
uv run mypy app/
```

## 🚀 Deployment

### Using Docker
```dockerfile
FROM python:3.13-slim
WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY gunicorn.conf.py .
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/

# Install dependencies
RUN uv sync --no-dev

# Run with Gunicorn
CMD ["uv", "run", "gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

### Using systemd (Ubuntu/Debian)
Create `/etc/systemd/system/pyfaststack.service`:
```ini
[Unit]
Description=PyFastStack Web Application
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/path/to/pyfaststack
Environment="PATH=/path/to/pyfaststack/.venv/bin"
ExecStart=/path/to/pyfaststack/.venv/bin/gunicorn app.main:app -c gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration
For production deployment behind Nginx:
- Supports 100MB client body size
- Optimized timeouts and buffers
- Gzip compression enabled
- WebSocket support included

## ⚡ Performance Optimizations

- **Fully Async** - Non-blocking operations throughout
- **Connection Pooling** - Efficient database connection reuse
- **Indexed Fields** - Optimized database queries
- **Worker Configuration** - Multi-worker setup for production
- **Request Pipelining** - Handle multiple requests efficiently
- **Response Compression** - Automatic GZip compression

### Performance Tuning

1. **Gunicorn Configuration** (`gunicorn.conf.py`):
   - Workers: CPU cores × 2 + 1
   - Worker connections: 10,000
   - Max requests per worker: 10,000
   - Timeout: 120 seconds

2. **Database Optimization**:
   - Connection pool size: 5-20 connections
   - Query optimization with proper indexes
   - Async operations for all database calls

3. **API Optimization**:
   - Pagination with configurable limits
   - Efficient serialization with Pydantic
   - Minimal overhead on health checks

## 🏃 Benchmarking

Test application performance using the `/health` endpoint:

```bash
# Using Apache Bench
ab -n 10000 -c 100 http://localhost:8000/health

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/health

# Using hey
hey -n 10000 -c 100 http://localhost:8000/health
```

The health endpoint is optimized for benchmarking:
- Minimal processing overhead
- No database queries
- No authentication checks
- Pure JSON response with timestamp

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Enhanced with [HTMX](https://htmx.org/)
- Database ORM by [SQLAlchemy](https://www.sqlalchemy.org/)
- Rate limiting by [SlowAPI](https://github.com/laurentS/slowapi)

---

**PyFastStack** - Modern Python web development made simple. FastAPI + Tailwind + HTMX = ⚡

Created with ❤️ by [George Khananaev](https://george.khananaev.com/)