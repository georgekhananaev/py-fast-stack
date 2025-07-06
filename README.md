# PyFastStack v1.0.0

Modern, production-ready Python web stack built with FastAPI, Tailwind CSS, and HTMX. Lightning-fast async architecture with JWT auth, real-time UI updates, and beautiful dark mode.

**Created by [George Khananaev](https://george.khananaev.com/)**

## 🚀 Features

### Core Tech Stack
- **FastAPI** - Lightning-fast async Python web framework
- **Tailwind CSS** - Modern utility-first CSS for beautiful UIs
- **HTMX** - Dynamic pages without writing JavaScript
- **Jinja2** - Fast and designer-friendly templating

### Developer Experience
- **100% Type Hints** - Full type safety with Pydantic validation
- **Async Everything** - Database, auth, even password hashing runs async
- **Auto API Docs** - Interactive Swagger UI and ReDoc out of the box
- **Hot Reload** - See changes instantly in development

### Production Ready
- **JWT Authentication** - Secure token-based auth system
- **Async SQLAlchemy 2.0** - Modern ORM with connection pooling
- **Gunicorn + Uvicorn** - Production-grade ASGI server setup
- **Dark/Light Mode** - Beautiful theme switching with CSS transitions

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
   git clone <repository-url>
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
   ```
   
   Update `.env` with your settings:
   - `SECRET_KEY`: Generate a secure secret key for production
   - `DATABASE_URL`: Database connection string (SQLite by default)

## 🚀 Running the Application

### Development Mode
```bash
uv run python run.py
# Or if uv environment is activated:
python run.py
```

On first run, the application will:
- Initialize the database automatically
- Create a root superuser with generated credentials
- Display credentials in colored output in the terminal

The application will be available at:
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

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
- `GET /health` - Health check endpoint (optimized for benchmarking)
  - Returns: `{"status": "healthy", "datetime": "2024-01-20T10:30:00", "timestamp": 1705749000.0}`
  - Minimal overhead for accurate performance testing
  - No database queries or authentication required

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns JWT token)
- `GET /api/v1/auth/me` - Get current user info

### Users (requires authentication)
- `GET /api/v1/users/` - List users (admin only)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user (admin only)


## 🧪 Testing

PyFastStack comes with tests for all the important stuff - auth, users, API endpoints, and performance.

### Important: Tests Require Running Server

**The tests connect to the actual running server, not a test server. You must start the server before running tests.**

### Step 1: Start the Server

In one terminal, start the server:
```bash
uv run python run.py
```

Note the root user credentials displayed.

### Step 2: Install Test Dependencies

```bash
# Install test dependencies
uv sync --extra test
```

### Step 3: Run Tests

In a separate terminal, while the server is running:

```bash
# Easy way - using the test runner script
uv run python run_tests.py

# Or manually with pytest
uv run pytest

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_auth.py -v

# Run specific test class or function
uv run pytest tests/test_users.py::TestUserOperations::test_list_users_as_superuser

# Run performance tests with detailed output
uv run pytest tests/test_performance.py -v -s
```

### Test Coverage

What's tested:

1. **Authentication Tests** (`test_auth.py`)
   - User registration (success, duplicate email/username)
   - Login (success, wrong password, inactive user)
   - Token validation
   - Current user endpoint

2. **User CRUD Tests** (`test_users.py`)
   - List users (with permissions check)
   - Get user by ID
   - Update user (with permissions)
   - Delete user (with protection for root user)
   - Profile updates and password changes

3. **Performance Tests** (`test_performance.py`)
   - Single request latency
   - Concurrent request handling
   - Authenticated endpoint performance
   - Database operation performance
   - Load testing with mixed endpoints
   - Stress testing (max requests/second)

### Performance Benchmarks

Run the performance tests to see detailed metrics:

```bash
# Run performance tests with output
uv run pytest tests/test_performance.py -v -s

# Example output:
# --- Concurrent Health Endpoint Test ---
# Total requests: 100
# Total time: 0.84s
# Requests/second: 119.05
# Avg response time: 35.21ms
# Min response time: 10.52ms
# Max response time: 68.94ms
```

### Benchmark Results

On a typical development machine, PyFastStack achieves:
- **Health endpoint**: 100-500+ requests/second
- **Authenticated endpoints**: 50-200 requests/second
- **Database operations**: 20-100 requests/second
- **Response times**: <50ms for health, <200ms for auth endpoints

### Writing New Tests

Tests use `pytest` with async support. Available fixtures:

- `client`: Async HTTP client for making requests
- `db_session`: Database session for test data
- `test_user`: Regular user fixture
- `test_superuser`: Admin user fixture
- `auth_headers`: Authentication headers for regular user
- `superuser_auth_headers`: Authentication headers for admin

Example test:
```python
@pytest.mark.asyncio
async def test_my_endpoint(client: AsyncClient, auth_headers: dict):
    response = await client.get("/my-endpoint", headers=auth_headers)
    assert response.status_code == 200
```

## 🧹 Code Quality

```bash
# Format code with Black
uv run black .

# Lint with Ruff
uv run ruff check .

# Type check with MyPy
uv run mypy app/
```

## 🔒 Security Features

- **Password Hashing** - Bcrypt with salt (the good stuff)
- **JWT Tokens** - Secure authentication tokens
- **CORS Protection** - Configure who can access your API
- **SQL Injection Protection** - SQLAlchemy handles this for you
- **Type Validation** - Pydantic catches bad data before it causes problems
- **HTTPS Ready** - Just add a reverse proxy
- **Async Password Hashing** - Won't block your other requests

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
Create `/etc/systemd/system/faststack.service`:
```ini
[Unit]
Description=PyFastStack Web Application
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/path/to/faststack
Environment="PATH=/path/to/pyfaststack/venv/bin"
ExecStart=/path/to/pyfaststack/.venv/bin/gunicorn app.main:app -c gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⚡ Performance Optimizations

- **Fully Async** - Nothing blocks, everything runs fast
- **Connection Pooling** - Reuses database connections smartly
- **Indexed Fields** - Common queries run faster
- **Non-blocking I/O** - Asyncio everywhere
- **Production Config** - Gunicorn with multiple workers ready to go
- **High Limits** - 10,000 concurrent connections? No problem
- **Large Files** - Upload up to 100MB
- **GZip** - Responses compressed automatically

## 📈 Request Limits and Performance Tuning

### Increased Limits Configuration

PyFastStack can handle serious traffic:

- **Max Request Body Size**: 100MB (configurable)
- **Max Concurrent Connections**: 10,000
- **Worker Connections**: 10,000 per worker
- **Request Timeout**: 120 seconds
- **Keep-Alive Timeout**: 5 seconds
- **Max Requests per Worker**: 10,000 before restart
- **API Pagination Limit**: Up to 10,000 items per page

### Customizing Limits

1. **Gunicorn Configuration** (`gunicorn.conf.py`):
   - `worker_connections`: Number of simultaneous connections per worker
   - `max_requests`: Requests before worker restart
   - `timeout`: Request timeout in seconds
   - `backlog`: Socket backlog size

2. **Application Level** (`app/main.py`):
   - Request body size limit in middleware
   - CORS and compression settings

3. **API Endpoints** (`app/api/v1/endpoints/`):
   - Pagination limits with Query parameters

### Running with Custom Uvicorn Config

```bash
# Use custom Uvicorn configuration for development
uv run python uvicorn_config.py
```

### Nginx Configuration

For production deployment behind Nginx, use the provided `nginx.conf.example`:
- Supports 100MB client body size
- Optimized timeouts and buffers
- Gzip compression enabled
- WebSocket support included

## 🏃 Benchmarking

Test the application's performance using the `/health` endpoint:

```bash
# Using Apache Bench (ab)
ab -n 10000 -c 100 http://localhost:8000/health

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/health

# Using hey
hey -n 10000 -c 100 http://localhost:8000/health
```

The health endpoint is made for benchmarking:
- Super fast response
- No database hits
- No auth checks
- Just JSON with timestamp

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Database ORM by [SQLAlchemy](https://www.sqlalchemy.org/)

---

**PyFastStack** - Modern Python web development made simple. FastAPI + Tailwind + HTMX = ⚡

Created with ❤️ by [George Khananaev](https://george.khananaev.com/)