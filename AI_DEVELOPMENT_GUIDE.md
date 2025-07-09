# AI Agent Development Guide for PyFastStack

This guide provides comprehensive instructions for AI agents to build new sections or features in PyFastStack while maintaining consistency with the existing architecture, security, and testing standards.

## 🏗️ Architecture Overview

### Tech Stack
- **Backend**: FastAPI (async Python web framework)
- **Database**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT tokens with Passlib bcrypt hashing
- **Frontend**: Jinja2 templates + HTMX + Tailwind CSS
- **Validation**: Pydantic for request/response schemas
- **Rate Limiting**: SlowAPI with IP-based limiting
- **Testing**: Pytest with async support

### Key Packages
```python
# Core dependencies
fastapi = "^0.104.1"
sqlalchemy = "^2.0.23"
asyncpg = "^0.29.0"          # For PostgreSQL
aiosqlite = "^0.19.0"        # For SQLite
python-jose = "^3.3.0"       # JWT handling
passlib = "^1.7.4"           # Password hashing
python-multipart = "^0.0.9"  # Form data
jinja2 = "^3.1.4"            # Templates
httpx = "^0.27.0"            # Async HTTP client
slowapi = "^0.1.9"           # Rate limiting
pydantic = "^2.5.2"          # Data validation
pydantic-settings = "^2.1.0" # Settings management
```

## 📁 Project Structure for New Features

When creating a new feature (e.g., "blog"), follow this structure:

```
app/
├── models/
│   └── blog.py          # SQLAlchemy model
├── schemas/
│   └── blog.py          # Pydantic schemas
├── crud/
│   └── blog.py          # Database operations
├── api/v1/endpoints/
│   └── blog.py          # API endpoints
├── web/
│   └── blog_routes.py   # Web UI routes
templates/
├── blog/
│   ├── list.html        # List view
│   ├── detail.html      # Detail view
│   └── form.html        # Create/edit form
tests/
└── test_blog.py         # Feature tests
```

## 🔐 Security Implementation

### 1. Authentication Flow

#### API Authentication (JWT)
```python
from fastapi import Depends, HTTPException, status
from app.api import deps

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(deps.get_current_active_user)
):
    """This endpoint requires a valid JWT token."""
    return {"user": current_user.username}
```

#### Web Authentication (Cookie-based)
```python
from app.core.auth_dependencies import get_current_user_from_cookie

@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Manual auth check for web routes
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user
    })
```

### 2. Rate Limiting

```python
from app.core.rate_limiter import limiter

@router.post("/create")
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def create_item(request: Request, ...):
    pass
```

Common rate limits:
- Login: 5/minute
- Registration: 3/minute
- Password changes: 3/minute
- Data creation: 10/minute
- General API: 60/minute

### 3. Permission Checks

```python
# Superuser only
async def admin_only(
    current_user: User = Depends(deps.get_current_active_superuser)
):
    return current_user

# Own resource or superuser
async def check_permission(user_id: int, current_user: User):
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
```

## 📝 Step-by-Step Feature Implementation

### Step 1: Create the Database Model

```python
# app/models/blog.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(String(500))
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="blog_posts")

# Don't forget to add to User model:
# blog_posts = relationship("BlogPost", back_populates="author")
```

### Step 2: Create Pydantic Schemas

```python
# app/schemas/blog.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.user import User

class BlogPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    is_published: bool = False

class BlogPostCreate(BlogPostBase):
    pass

class BlogPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    is_published: Optional[bool] = None

class BlogPostInDB(BlogPostBase):
    id: int
    slug: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BlogPost(BlogPostInDB):
    author: User
```

### Step 3: Create CRUD Operations

```python
# app/crud/blog.py
from typing import List, Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.blog import BlogPost
from app.schemas.blog import BlogPostCreate, BlogPostUpdate
from app.utils.slug import generate_unique_slug

class CRUDBlog(CRUDBase[BlogPost, BlogPostCreate, BlogPostUpdate]):
    async def create_with_author(
        self, db: AsyncSession, *, obj_in: BlogPostCreate, author_id: int
    ) -> BlogPost:
        """Create blog post with author."""
        db_obj = BlogPost(
            **obj_in.model_dump(),
            author_id=author_id,
            slug=await generate_unique_slug(db, obj_in.title, BlogPost)
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_published(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 10
    ) -> List[BlogPost]:
        """Get published blog posts."""
        query = (
            select(BlogPost)
            .where(BlogPost.is_published == True)
            .options(selectinload(BlogPost.author))
            .order_by(BlogPost.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_slug(
        self, db: AsyncSession, *, slug: str
    ) -> Optional[BlogPost]:
        """Get blog post by slug."""
        query = (
            select(BlogPost)
            .where(BlogPost.slug == slug)
            .options(selectinload(BlogPost.author))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

blog = CRUDBlog(BlogPost)
```

### Step 4: Create API Endpoints

```python
# app/api/v1/endpoints/blog.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import blog as crud_blog
from app.schemas.blog import BlogPost, BlogPostCreate, BlogPostUpdate
from app.models.user import User
from app.core.rate_limiter import limiter

router = APIRouter()

@router.get("/", response_model=List[BlogPost])
async def list_posts(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(deps.get_db)
):
    """List published blog posts - Public endpoint."""
    posts = await crud_blog.get_published(db, skip=skip, limit=limit)
    return posts

@router.get("/{slug}", response_model=BlogPost)
async def get_post(
    slug: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """Get blog post by slug - Public endpoint."""
    post = await crud_blog.get_by_slug(db, slug=slug)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Blog post not found"
        )
    if not post.is_published and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="This post is not published"
        )
    return post

@router.post("/", response_model=BlogPost, status_code=201)
@limiter.limit("10/minute")
async def create_post(
    request: Request,
    post_in: BlogPostCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Create new blog post - Requires authentication."""
    post = await crud_blog.create_with_author(
        db, obj_in=post_in, author_id=current_user.id
    )
    return post

@router.put("/{id}", response_model=BlogPost)
async def update_post(
    id: int,
    post_in: BlogPostUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Update blog post - Author or superuser only."""
    post = await crud_blog.get(db, id=id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions
    if post.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    post = await crud_blog.update(db, db_obj=post, obj_in=post_in)
    return post

@router.delete("/{id}")
async def delete_post(
    id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """Delete blog post - Superuser only."""
    post = await crud_blog.get(db, id=id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    await crud_blog.remove(db, id=id)
    return {"detail": "Post deleted successfully"}
```

### Step 5: Create Web Routes

```python
# app/web/blog_routes.py
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth_dependencies import get_current_user_from_cookie
from app.crud import blog as crud_blog
from app.schemas.blog import BlogPostCreate, BlogPostUpdate
from app.db.session import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/blog", response_class=HTMLResponse)
async def blog_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = 1
):
    """Blog listing page - Public."""
    skip = (page - 1) * 10
    posts = await crud_blog.get_published(db, skip=skip, limit=10)
    
    return templates.TemplateResponse("blog/list.html", {
        "request": request,
        "posts": posts,
        "page": page
    })

@router.get("/blog/new", response_class=HTMLResponse)
async def blog_new(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create new blog post form - Requires auth."""
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("blog/form.html", {
        "request": request,
        "user": current_user,
        "title": "New Post"
    })

@router.post("/blog/new")
async def blog_create(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    summary: str = Form(None),
    is_published: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    """Handle blog post creation."""
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        post_in = BlogPostCreate(
            title=title,
            content=content,
            summary=summary,
            is_published=is_published
        )
        post = await crud_blog.create_with_author(
            db, obj_in=post_in, author_id=current_user.id
        )
        return RedirectResponse(
            url=f"/blog/{post.slug}",
            status_code=302
        )
    except Exception as e:
        return templates.TemplateResponse("blog/form.html", {
            "request": request,
            "user": current_user,
            "error": str(e),
            "title": "New Post"
        })
```

### Step 6: Create Templates

```html
<!-- templates/blog/list.html -->
{% extends "layouts/base.html" %}

{% block content %}
<div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8">Blog Posts</h1>
    
    {% if user %}
    <a href="/blog/new" class="btn btn-primary mb-6">
        Create New Post
    </a>
    {% endif %}
    
    <div class="space-y-6">
        {% for post in posts %}
        <article class="bg-white dark:bg-slate-800 rounded-lg p-6 shadow">
            <h2 class="text-2xl font-semibold mb-2">
                <a href="/blog/{{ post.slug }}" class="hover:text-primary-600">
                    {{ post.title }}
                </a>
            </h2>
            <p class="text-slate-600 dark:text-slate-400 mb-2">
                By {{ post.author.full_name or post.author.username }} • 
                {{ post.created_at.strftime('%B %d, %Y') }}
            </p>
            {% if post.summary %}
            <p class="text-slate-700 dark:text-slate-300">
                {{ post.summary }}
            </p>
            {% endif %}
        </article>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

### Step 7: Add Routes to Main Application

```python
# app/api/v1/api.py
from app.api.v1.endpoints import blog

api_router.include_router(
    blog.router,
    prefix="/blog",
    tags=["📝 Blog"]
)

# app/web/__init__.py
from app.web import blog_routes

# In main.py
app.include_router(blog_routes.router, tags=["📝 Blog Pages"])
```

### Step 8: Create Tests

```python
# tests/test_blog.py
import pytest
from httpx import AsyncClient
from app.models.user import User

class TestBlogAPI:
    @pytest.mark.asyncio
    async def test_create_blog_post(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a blog post."""
        data = {
            "title": "Test Post",
            "content": "This is test content",
            "summary": "Test summary",
            "is_published": True
        }
        response = await client.post(
            "/api/v1/blog/",
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 201
        content = response.json()
        assert content["title"] == data["title"]
        assert content["slug"] == "test-post"
        assert "id" in content
    
    @pytest.mark.asyncio
    async def test_list_published_posts(self, client: AsyncClient):
        """Test listing published posts."""
        response = await client.get("/api/v1/blog/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_get_post_by_slug(
        self, client: AsyncClient, test_blog_post: dict
    ):
        """Test getting post by slug."""
        response = await client.get(f"/api/v1/blog/{test_blog_post['slug']}")
        assert response.status_code == 200
        assert response.json()["id"] == test_blog_post["id"]
    
    @pytest.mark.asyncio
    async def test_update_own_post(
        self, client: AsyncClient, auth_headers: dict, test_blog_post: dict
    ):
        """Test updating own blog post."""
        update_data = {"title": "Updated Title"}
        response = await client.put(
            f"/api/v1/blog/{test_blog_post['id']}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_delete_post_superuser_only(
        self, client: AsyncClient, 
        auth_headers: dict,
        superuser_auth_headers: dict,
        test_blog_post: dict
    ):
        """Test that only superuser can delete posts."""
        # Regular user should fail
        response = await client.delete(
            f"/api/v1/blog/{test_blog_post['id']}",
            headers=auth_headers
        )
        assert response.status_code == 403
        
        # Superuser should succeed
        response = await client.delete(
            f"/api/v1/blog/{test_blog_post['id']}",
            headers=superuser_auth_headers
        )
        assert response.status_code == 200

class TestBlogWeb:
    @pytest.mark.asyncio
    async def test_blog_list_page(self, client: AsyncClient):
        """Test blog listing page."""
        response = await client.get("/blog")
        assert response.status_code == 200
        assert "Blog Posts" in response.text
    
    @pytest.mark.asyncio
    async def test_create_post_requires_auth(self, client: AsyncClient):
        """Test that creating post requires authentication."""
        response = await client.get("/blog/new")
        assert response.status_code == 303  # Redirect to login
    
    @pytest.mark.asyncio
    async def test_create_post_form(
        self, client: AsyncClient, auth_cookies: dict
    ):
        """Test blog post creation via web form."""
        response = await client.post(
            "/blog/new",
            data={
                "title": "Web Test Post",
                "content": "Content from web",
                "summary": "Web summary",
                "is_published": "on"
            },
            cookies=auth_cookies
        )
        assert response.status_code == 302  # Redirect to post
```

### Step 9: Add Test Fixtures

```python
# tests/conftest.py
@pytest_asyncio.fixture
async def test_blog_post(client: AsyncClient, auth_headers: dict) -> dict:
    """Create a test blog post."""
    data = {
        "title": "Test Blog Post",
        "content": "This is test content for testing.",
        "summary": "Test summary",
        "is_published": True
    }
    response = await client.post(
        "/api/v1/blog/",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()
```

## 🧪 Testing Requirements

### Test Coverage Must Include:

1. **API Tests**
   - CRUD operations (Create, Read, Update, Delete)
   - Permission checks (who can do what)
   - Invalid data handling
   - Rate limiting verification
   - Authentication requirements

2. **Web UI Tests**
   - Page rendering
   - Form submissions
   - Authentication redirects
   - Error handling
   - Cookie-based auth

3. **Security Tests**
   - Unauthorized access attempts
   - Permission boundary testing
   - Rate limit effectiveness
   - Input validation

4. **Performance Tests** (for data-heavy features)
   - Response time under load
   - Concurrent request handling
   - Database query optimization

### Running Tests
```bash
# Run all tests for your feature
uv run pytest tests/test_blog.py -v

# Run with coverage
uv run pytest tests/test_blog.py --cov=app.api.v1.endpoints.blog --cov=app.crud.blog

# Run specific test
uv run pytest tests/test_blog.py::TestBlogAPI::test_create_blog_post
```

## ⚠️ Common Pitfalls to Avoid

1. **Forgetting Rate Limiting** - Add rate limits to prevent abuse
2. **Missing Permission Checks** - Always verify user permissions
3. **Synchronous Operations** - Use async/await everywhere
4. **N+1 Queries** - Use selectinload for relationships
5. **Missing Indexes** - Add indexes for frequently queried fields
6. **Hardcoded Strings** - Use constants and environment variables
7. **Missing Error Handling** - Handle all exceptions gracefully
8. **Skipping Tests** - Test every endpoint and edge case

## 🎯 Error Handling Standards

### API Error Responses
```python
from fastapi import HTTPException

# Not found
raise HTTPException(status_code=404, detail="Resource not found")

# Forbidden
raise HTTPException(status_code=403, detail="Not enough permissions")

# Bad request
raise HTTPException(status_code=400, detail="Invalid input data")

# Conflict
raise HTTPException(status_code=409, detail="Resource already exists")

# Rate limited (handled by SlowAPI automatically)
# Returns: {"error": "Rate limit exceeded: X per Y minute"}
```

### Web Error Handling
```python
# In templates, show errors gracefully
return templates.TemplateResponse("form.html", {
    "request": request,
    "error": "An error occurred. Please try again.",
    "user": current_user
})
```

## 📋 Checklist for New Features

- [ ] Database model created with proper indexes
- [ ] Pydantic schemas for validation
- [ ] CRUD operations implemented
- [ ] API endpoints with proper authentication
- [ ] Rate limiting on sensitive endpoints
- [ ] Web routes for UI (if applicable)
- [ ] Templates following existing design
- [ ] Permission checks implemented
- [ ] Error handling for all edge cases
- [ ] Tests for all functionality
- [ ] Documentation in docstrings
- [ ] Routes added to main application
- [ ] Database migrations (if needed)
- [ ] Update README.md with new endpoints

## 🔄 Database Migrations

When adding new models or modifying existing ones:

```python
# The app automatically creates tables on startup
# For production, consider using Alembic for migrations

# 1. Install alembic
uv add alembic

# 2. Initialize alembic
alembic init alembic

# 3. Create migration
alembic revision --autogenerate -m "Add blog posts table"

# 4. Apply migration
alembic upgrade head
```

## 📦 Adding Dependencies

If your feature needs new packages:

```bash
# Add to project
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update all team members
uv sync
```

## 🚀 Final Steps

1. **Test Everything**
   ```bash
   # Run all tests
   uv run pytest
   
   # Check code quality
   uv run black .
   uv run ruff check .
   ```

2. **Update Documentation**
   - Add new endpoints to README.md
   - Update API documentation
   - Add usage examples

3. **Security Review**
   - Verify all endpoints have proper authentication
   - Check rate limiting is appropriate
   - Ensure no sensitive data is exposed
   - Validate all user inputs

4. **Performance Check**
   - Test with realistic data volumes
   - Check database query performance
   - Verify async operations are used

Remember: Consistency is key. Follow existing patterns and conventions throughout the codebase.