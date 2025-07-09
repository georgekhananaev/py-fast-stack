# MCP Server Implementation for PyFastStack

## Overview

The Model Context Protocol (MCP) is an open protocol that enables seamless integration between AI assistants and external data sources. This guide provides comprehensive instructions for implementing an MCP server in PyFastStack to serve blobs, database content, and other application data to AI agents.

## Architecture Design

### Core Components

```
PyFastStack Application
├── MCP Server Layer
│   ├── Transport (stdio/SSE)
│   ├── Protocol Handler
│   ├── Resource Provider
│   └── Tool Provider
├── Data Access Layer
│   ├── Blob Storage
│   ├── Database Access
│   └── File System
└── Security Layer
    ├── Authentication
    └── Authorization
```

## Implementation Guide

### Phase 1: MCP Server Foundation

#### 1.1 Install MCP SDK
```bash
pip install mcp-server-sdk
```

#### 1.2 Create MCP Server Module
**File: `app/mcp/server.py`**

```python
import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from mcp.server import Server, Request, Response
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    ResourceContent,
    Tool,
    ToolResult,
    TextContent,
    ImageContent,
    BlobContent
)

from app.db.session import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.core.config import get_settings

settings = get_settings()

class PyFastStackMCPServer:
    def __init__(self):
        self.server = Server("pyfaststack-mcp")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Register all MCP handlers."""
        # Resource handlers
        self.server.list_resources.handler(self.handle_list_resources)
        self.server.read_resource.handler(self.handle_read_resource)
        
        # Tool handlers
        self.server.list_tools.handler(self.handle_list_tools)
        self.server.call_tool.handler(self.handle_call_tool)
        
        # Prompt handlers
        self.server.list_prompts.handler(self.handle_list_prompts)
        self.server.get_prompt.handler(self.handle_get_prompt)
    
    async def handle_list_resources(self, request: Request) -> List[Resource]:
        """List all available resources."""
        resources = [
            Resource(
                uri="pyfaststack://users",
                name="Users",
                description="Access user data from the database",
                mimeType="application/json"
            ),
            Resource(
                uri="pyfaststack://subscriptions",
                name="Subscriptions",
                description="Access subscription data",
                mimeType="application/json"
            ),
            Resource(
                uri="pyfaststack://blobs",
                name="Blob Storage",
                description="Access uploaded files and blobs",
                mimeType="application/octet-stream"
            ),
            Resource(
                uri="pyfaststack://config",
                name="Application Configuration",
                description="Read application configuration",
                mimeType="application/json"
            ),
            Resource(
                uri="pyfaststack://templates",
                name="HTML Templates",
                description="Access Jinja2 templates",
                mimeType="text/html"
            ),
            Resource(
                uri="pyfaststack://static",
                name="Static Files",
                description="Access static assets (CSS, JS, images)",
                mimeType="*/*"
            )
        ]
        return resources
    
    async def handle_read_resource(self, request: Request) -> ResourceContent:
        """Read a specific resource."""
        uri = request.params["uri"]
        
        if uri == "pyfaststack://users":
            return await self._read_users()
        elif uri == "pyfaststack://subscriptions":
            return await self._read_subscriptions()
        elif uri.startswith("pyfaststack://blobs/"):
            return await self._read_blob(uri)
        elif uri == "pyfaststack://config":
            return await self._read_config()
        elif uri.startswith("pyfaststack://templates/"):
            return await self._read_template(uri)
        elif uri.startswith("pyfaststack://static/"):
            return await self._read_static(uri)
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    async def _read_users(self) -> ResourceContent:
        """Read user data from database."""
        async with get_db() as db:
            users = db.query(User).all()
            user_data = [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ]
        
        return ResourceContent(
            uri="pyfaststack://users",
            mimeType="application/json",
            content=TextContent(text=json.dumps(user_data, indent=2))
        )
    
    async def _read_subscriptions(self) -> ResourceContent:
        """Read subscription data."""
        async with get_db() as db:
            subs = db.query(Subscription).all()
            sub_data = [
                {
                    "id": sub.id,
                    "email": sub.email,
                    "is_active": sub.is_active,
                    "created_at": sub.created_at.isoformat() if sub.created_at else None
                }
                for sub in subs
            ]
        
        return ResourceContent(
            uri="pyfaststack://subscriptions",
            mimeType="application/json",
            content=TextContent(text=json.dumps(sub_data, indent=2))
        )
    
    async def _read_blob(self, uri: str) -> ResourceContent:
        """Read blob data from storage."""
        blob_path = uri.replace("pyfaststack://blobs/", "")
        file_path = Path(settings.upload_dir) / blob_path
        
        if not file_path.exists():
            raise ValueError(f"Blob not found: {blob_path}")
        
        # Determine mime type
        mime_type = "application/octet-stream"
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            mime_type = f"image/{file_path.suffix[1:]}"
        elif file_path.suffix.lower() == '.pdf':
            mime_type = "application/pdf"
        elif file_path.suffix.lower() in ['.txt', '.md']:
            mime_type = "text/plain"
        
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Return appropriate content type
        if mime_type.startswith('image/'):
            return ResourceContent(
                uri=uri,
                mimeType=mime_type,
                content=ImageContent(
                    data=content.hex(),
                    mimeType=mime_type
                )
            )
        elif mime_type == "text/plain":
            return ResourceContent(
                uri=uri,
                mimeType=mime_type,
                content=TextContent(text=content.decode('utf-8'))
            )
        else:
            return ResourceContent(
                uri=uri,
                mimeType=mime_type,
                content=BlobContent(
                    data=content.hex(),
                    mimeType=mime_type
                )
            )
    
    async def _read_config(self) -> ResourceContent:
        """Read application configuration."""
        config_data = {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "debug": settings.debug,
            "database_url": "***hidden***",
            "cors_origins": settings.cors_origins,
            "features": {
                "authentication": True,
                "file_upload": True,
                "rate_limiting": True,
                "caching": False
            }
        }
        
        return ResourceContent(
            uri="pyfaststack://config",
            mimeType="application/json",
            content=TextContent(text=json.dumps(config_data, indent=2))
        )
    
    async def _read_template(self, uri: str) -> ResourceContent:
        """Read HTML template."""
        template_path = uri.replace("pyfaststack://templates/", "")
        file_path = Path("templates") / template_path
        
        if not file_path.exists():
            raise ValueError(f"Template not found: {template_path}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        return ResourceContent(
            uri=uri,
            mimeType="text/html",
            content=TextContent(text=content)
        )
    
    async def _read_static(self, uri: str) -> ResourceContent:
        """Read static file."""
        static_path = uri.replace("pyfaststack://static/", "")
        file_path = Path("static") / static_path
        
        if not file_path.exists():
            raise ValueError(f"Static file not found: {static_path}")
        
        # Determine mime type
        mime_map = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp'
        }
        mime_type = mime_map.get(file_path.suffix.lower(), 'application/octet-stream')
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        if mime_type.startswith('text/') or mime_type == 'application/javascript':
            return ResourceContent(
                uri=uri,
                mimeType=mime_type,
                content=TextContent(text=content.decode('utf-8'))
            )
        else:
            return ResourceContent(
                uri=uri,
                mimeType=mime_type,
                content=BlobContent(
                    data=content.hex(),
                    mimeType=mime_type
                )
            )
    
    async def handle_list_tools(self, request: Request) -> List[Tool]:
        """List available tools."""
        tools = [
            Tool(
                name="search_users",
                description="Search for users by username or email",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="create_subscription",
                description="Create a new newsletter subscription",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address to subscribe"
                        }
                    },
                    "required": ["email"]
                }
            ),
            Tool(
                name="analyze_template",
                description="Analyze a template for SEO issues",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "description": "Name of the template file"
                        }
                    },
                    "required": ["template_name"]
                }
            ),
            Tool(
                name="upload_blob",
                description="Upload a file to blob storage",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Name for the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Base64 encoded file content"
                        },
                        "mime_type": {
                            "type": "string",
                            "description": "MIME type of the file"
                        }
                    },
                    "required": ["filename", "content", "mime_type"]
                }
            )
        ]
        return tools
    
    async def handle_call_tool(self, request: Request) -> ToolResult:
        """Execute a tool."""
        tool_name = request.params["name"]
        arguments = request.params.get("arguments", {})
        
        if tool_name == "search_users":
            return await self._search_users(arguments["query"])
        elif tool_name == "create_subscription":
            return await self._create_subscription(arguments["email"])
        elif tool_name == "analyze_template":
            return await self._analyze_template(arguments["template_name"])
        elif tool_name == "upload_blob":
            return await self._upload_blob(
                arguments["filename"],
                arguments["content"],
                arguments["mime_type"]
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _search_users(self, query: str) -> ToolResult:
        """Search for users."""
        async with get_db() as db:
            users = db.query(User).filter(
                (User.username.contains(query)) | 
                (User.email.contains(query))
            ).all()
            
            results = [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
                for user in users
            ]
        
        return ToolResult(
            content=TextContent(
                text=json.dumps({
                    "query": query,
                    "count": len(results),
                    "results": results
                }, indent=2)
            )
        )
    
    async def _create_subscription(self, email: str) -> ToolResult:
        """Create a newsletter subscription."""
        async with get_db() as db:
            # Check if already exists
            existing = db.query(Subscription).filter_by(email=email).first()
            if existing:
                return ToolResult(
                    content=TextContent(
                        text=json.dumps({
                            "success": False,
                            "message": "Email already subscribed"
                        }, indent=2)
                    )
                )
            
            # Create new subscription
            sub = Subscription(email=email)
            db.add(sub)
            db.commit()
            
            return ToolResult(
                content=TextContent(
                    text=json.dumps({
                        "success": True,
                        "message": "Successfully subscribed",
                        "subscription_id": sub.id
                    }, indent=2)
                )
            )
    
    async def _analyze_template(self, template_name: str) -> ToolResult:
        """Analyze a template for SEO issues."""
        template_path = Path("templates") / template_name
        
        if not template_path.exists():
            return ToolResult(
                content=TextContent(
                    text=json.dumps({
                        "error": f"Template not found: {template_name}"
                    }, indent=2)
                )
            )
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Simple SEO analysis
        issues = []
        
        if '<title>' not in content and '{% block title %}' not in content:
            issues.append("Missing title tag")
        
        if 'meta name="description"' not in content:
            issues.append("Missing meta description")
        
        if 'og:title' not in content:
            issues.append("Missing Open Graph tags")
        
        if 'alt=' not in content and '<img' in content:
            issues.append("Images may be missing alt attributes")
        
        return ToolResult(
            content=TextContent(
                text=json.dumps({
                    "template": template_name,
                    "issues": issues,
                    "issue_count": len(issues),
                    "status": "good" if len(issues) == 0 else "needs improvement"
                }, indent=2)
            )
        )
    
    async def _upload_blob(self, filename: str, content: str, mime_type: str) -> ToolResult:
        """Upload a file to blob storage."""
        import base64
        
        # Decode base64 content
        try:
            file_data = base64.b64decode(content)
        except Exception as e:
            return ToolResult(
                content=TextContent(
                    text=json.dumps({
                        "success": False,
                        "error": f"Invalid base64 content: {str(e)}"
                    }, indent=2)
                )
            )
        
        # Save to upload directory
        upload_path = Path(settings.upload_dir) / filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(upload_path, 'wb') as f:
            f.write(file_data)
        
        return ToolResult(
            content=TextContent(
                text=json.dumps({
                    "success": True,
                    "filename": filename,
                    "size": len(file_data),
                    "mime_type": mime_type,
                    "uri": f"pyfaststack://blobs/{filename}"
                }, indent=2)
            )
        )
    
    async def handle_list_prompts(self, request: Request) -> List[Dict[str, Any]]:
        """List available prompts."""
        prompts = [
            {
                "name": "analyze_seo",
                "description": "Analyze the application for SEO improvements",
                "arguments": []
            },
            {
                "name": "generate_sitemap",
                "description": "Generate a sitemap.xml file",
                "arguments": [
                    {
                        "name": "base_url",
                        "description": "Base URL of the website",
                        "required": True
                    }
                ]
            },
            {
                "name": "optimize_images",
                "description": "Suggest image optimization strategies",
                "arguments": []
            }
        ]
        return prompts
    
    async def handle_get_prompt(self, request: Request) -> Dict[str, Any]:
        """Get a specific prompt."""
        prompt_name = request.params["name"]
        arguments = request.params.get("arguments", {})
        
        if prompt_name == "analyze_seo":
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": "Analyze the PyFastStack application for SEO improvements. Check all templates, look for missing meta tags, and suggest improvements."
                    }
                ]
            }
        elif prompt_name == "generate_sitemap":
            base_url = arguments.get("base_url", "https://example.com")
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Generate a sitemap.xml file for PyFastStack with base URL: {base_url}. Include all public pages and appropriate metadata."
                    }
                ]
            }
        elif prompt_name == "optimize_images":
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": "Analyze all images in the static directory and suggest optimization strategies for better web performance."
                    }
                ]
            }
        else:
            raise ValueError(f"Unknown prompt: {prompt_name}")
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


async def main():
    """Main entry point for MCP server."""
    server = PyFastStackMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
```

### Phase 2: Integration with PyFastStack

#### 2.1 Create MCP Configuration
**File: `app/core/mcp_config.py`**

```python
from pydantic import BaseModel
from typing import List, Optional

class MCPConfig(BaseModel):
    """MCP server configuration."""
    enabled: bool = True
    transport: str = "stdio"  # or "sse" for server-sent events
    allowed_resources: List[str] = ["*"]
    allowed_tools: List[str] = ["*"]
    max_blob_size: int = 10 * 1024 * 1024  # 10MB
    rate_limit: Optional[int] = 100  # requests per minute
    
    # Security settings
    require_auth: bool = True
    allowed_clients: List[str] = []  # Client IDs or patterns
    
    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
```

#### 2.2 Add MCP Endpoints to FastAPI
**File: `app/api/v1/endpoints/mcp.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio

from app.core.auth_dependencies import get_current_user
from app.mcp.server import PyFastStackMCPServer

router = APIRouter()

@router.get("/mcp/resources")
async def list_mcp_resources(
    current_user = Depends(get_current_user)
):
    """List available MCP resources."""
    server = PyFastStackMCPServer()
    resources = await server.handle_list_resources(None)
    return {
        "resources": [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mimeType": r.mimeType
            }
            for r in resources
        ]
    }

@router.get("/mcp/resources/{resource_path:path}")
async def read_mcp_resource(
    resource_path: str,
    current_user = Depends(get_current_user)
):
    """Read a specific MCP resource."""
    server = PyFastStackMCPServer()
    uri = f"pyfaststack://{resource_path}"
    
    try:
        content = await server.handle_read_resource(
            Request(params={"uri": uri})
        )
        
        # Convert content based on type
        if hasattr(content.content, 'text'):
            return {
                "uri": content.uri,
                "mimeType": content.mimeType,
                "content": content.content.text
            }
        elif hasattr(content.content, 'data'):
            return {
                "uri": content.uri,
                "mimeType": content.mimeType,
                "content": content.content.data,
                "encoding": "hex"
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/mcp/sse")
async def mcp_server_sent_events(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Server-sent events endpoint for MCP."""
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        client_id = f"client_{current_user.id}"
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'client_id': client_id})}\n\n"
        
        # Keep connection alive and handle MCP messages
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                # Send heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
        except asyncio.CancelledError:
            # Clean up on disconnect
            pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )

@router.post("/mcp/tools/{tool_name}")
async def call_mcp_tool(
    tool_name: str,
    arguments: dict,
    current_user = Depends(get_current_user)
):
    """Call an MCP tool."""
    server = PyFastStackMCPServer()
    
    try:
        result = await server.handle_call_tool(
            Request(params={
                "name": tool_name,
                "arguments": arguments
            })
        )
        
        # Extract result content
        if hasattr(result.content, 'text'):
            return json.loads(result.content.text)
        else:
            return {"result": str(result.content)}
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 3: Advanced Features

#### 3.1 Blob Storage Handler
**File: `app/mcp/blob_handler.py`**

```python
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib
import mimetypes
from datetime import datetime

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.blob import Blob  # You'll need to create this model

class BlobHandler:
    """Handle blob storage for MCP."""
    
    def __init__(self, storage_path: str = "uploads"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    async def store_blob(
        self,
        content: bytes,
        filename: str,
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a blob and return its URI."""
        # Calculate hash
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Determine mime type if not provided
        if not mime_type:
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Create subdirectory based on hash prefix
        subdir = self.storage_path / content_hash[:2] / content_hash[2:4]
        subdir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = subdir / content_hash
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Store metadata in database
        async with get_db() as db:
            blob = Blob(
                hash=content_hash,
                filename=filename,
                mime_type=mime_type,
                size=len(content),
                storage_path=str(file_path),
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            db.add(blob)
            db.commit()
        
        return f"pyfaststack://blobs/{content_hash}"
    
    async def retrieve_blob(self, blob_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve a blob by its hash."""
        async with get_db() as db:
            blob = db.query(Blob).filter_by(hash=blob_hash).first()
            if not blob:
                return None
            
            # Read file content
            with open(blob.storage_path, 'rb') as f:
                content = f.read()
            
            return {
                "content": content,
                "filename": blob.filename,
                "mime_type": blob.mime_type,
                "size": blob.size,
                "metadata": blob.metadata,
                "created_at": blob.created_at
            }
    
    async def list_blobs(
        self,
        mime_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List blobs with optional filtering."""
        async with get_db() as db:
            query = db.query(Blob)
            
            if mime_type:
                query = query.filter(Blob.mime_type.like(f"{mime_type}%"))
            
            blobs = query.offset(offset).limit(limit).all()
            
            return [
                {
                    "uri": f"pyfaststack://blobs/{blob.hash}",
                    "filename": blob.filename,
                    "mime_type": blob.mime_type,
                    "size": blob.size,
                    "created_at": blob.created_at.isoformat()
                }
                for blob in blobs
            ]
```

#### 3.2 Create Blob Model
**File: `app/models/blob.py`**

```python
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from app.db.base_class import Base
from datetime import datetime

class Blob(Base):
    __tablename__ = "blobs"
    
    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String(64), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    storage_path = Column(Text, nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Phase 4: Client Integration

#### 4.1 MCP Client Library
**File: `app/mcp/client.py`**

```python
import aiohttp
import json
from typing import Dict, Any, Optional, List
from app.core.config import get_settings

settings = get_settings()

class MCPClient:
    """Client for interacting with MCP servers."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        async with self.session.get(f"{self.base_url}/mcp/resources") as resp:
            data = await resp.json()
            return data["resources"]
    
    async def read_resource(self, resource_path: str) -> Dict[str, Any]:
        """Read a specific resource."""
        async with self.session.get(f"{self.base_url}/mcp/resources/{resource_path}") as resp:
            return await resp.json()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool."""
        async with self.session.post(
            f"{self.base_url}/mcp/tools/{tool_name}",
            json=arguments
        ) as resp:
            return await resp.json()
    
    async def upload_blob(self, filename: str, content: bytes, mime_type: str) -> str:
        """Upload a blob and return its URI."""
        import base64
        
        result = await self.call_tool("upload_blob", {
            "filename": filename,
            "content": base64.b64encode(content).decode('utf-8'),
            "mime_type": mime_type
        })
        
        return result["uri"]
```

### Phase 5: Security & Authentication

#### 5.1 MCP Authentication Middleware
**File: `app/core/mcp_auth.py`**

```python
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.models.user import User
from app.db.session import get_db

settings = get_settings()
security = HTTPBearer()

class MCPAuth:
    """MCP-specific authentication handler."""
    
    @staticmethod
    def create_mcp_token(user_id: int, client_id: str) -> str:
        """Create an MCP-specific token."""
        payload = {
            "user_id": user_id,
            "client_id": client_id,
            "type": "mcp_access",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            settings.secret_key,
            algorithm="HS256"
        )
    
    @staticmethod
    async def verify_mcp_token(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """Verify MCP token."""
        token = credentials.credentials
        
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=["HS256"]
            )
            
            if payload.get("type") != "mcp_access":
                raise HTTPException(
                    status_code=403,
                    detail="Invalid token type"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
    
    @staticmethod
    async def get_mcp_user(
        token_data: Dict[str, Any] = Depends(verify_mcp_token)
    ) -> User:
        """Get user from MCP token."""
        async with get_db() as db:
            user = db.query(User).filter_by(id=token_data["user_id"]).first()
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            return user
```

## Usage Examples

### 1. Using MCP from Claude Desktop

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "pyfaststack": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost/db"
      }
    }
  }
}
```

### 2. Using MCP from Python

```python
from app.mcp.client import MCPClient

async def example_usage():
    async with MCPClient("http://localhost:8000", api_key="your-key") as client:
        # List resources
        resources = await client.list_resources()
        print(f"Available resources: {len(resources)}")
        
        # Read users
        users = await client.read_resource("users")
        print(f"Users: {users}")
        
        # Upload a file
        with open("document.pdf", "rb") as f:
            blob_uri = await client.upload_blob(
                "document.pdf",
                f.read(),
                "application/pdf"
            )
        print(f"Uploaded: {blob_uri}")
        
        # Search users
        results = await client.call_tool("search_users", {"query": "admin"})
        print(f"Search results: {results}")
```

### 3. Using MCP via REST API

```bash
# Get MCP token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/mcp-token \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"client_id": "my-ai-agent"}' \
  | jq -r .token)

# List resources
curl http://localhost:8000/api/v1/mcp/resources \
  -H "Authorization: Bearer $TOKEN"

# Read a resource
curl http://localhost:8000/api/v1/mcp/resources/users \
  -H "Authorization: Bearer $TOKEN"

# Call a tool
curl -X POST http://localhost:8000/api/v1/mcp/tools/search_users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "john"}'
```

## Deployment Considerations

### 1. Production Configuration

```python
# app/core/config.py additions
class Settings:
    # ... existing settings ...
    
    # MCP Settings
    mcp_enabled: bool = True
    mcp_transport: str = "stdio"  # or "sse", "websocket"
    mcp_max_blob_size: int = 100 * 1024 * 1024  # 100MB
    mcp_rate_limit: int = 1000  # requests per minute
    mcp_cache_ttl: int = 300  # 5 minutes
    
    # MCP Security
    mcp_require_auth: bool = True
    mcp_allowed_origins: List[str] = ["https://ai.example.com"]
    mcp_token_expiry: int = 86400  # 24 hours
```

### 2. Docker Support

```dockerfile
# Add to Dockerfile
RUN pip install mcp-server-sdk

# Add MCP server command
CMD ["python", "-m", "app.mcp.server"]
```

### 3. Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pyfaststack-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pyfaststack-mcp
  template:
    metadata:
      labels:
        app: pyfaststack-mcp
    spec:
      containers:
      - name: mcp-server
        image: pyfaststack:latest
        command: ["python", "-m", "app.mcp.server"]
        env:
        - name: MCP_TRANSPORT
          value: "sse"
        ports:
        - containerPort: 8001
          name: mcp
---
apiVersion: v1
kind: Service
metadata:
  name: pyfaststack-mcp-service
spec:
  selector:
    app: pyfaststack-mcp
  ports:
  - port: 8001
    targetPort: mcp
```

## Best Practices

### 1. Resource Naming Convention
- Use consistent URI scheme: `pyfaststack://category/identifier`
- Categories: users, blobs, config, templates, static, data
- Examples:
  - `pyfaststack://users/123`
  - `pyfaststack://blobs/abc123def456`
  - `pyfaststack://templates/index.html`

### 2. Error Handling
- Always return structured error responses
- Include error codes and descriptions
- Log errors for monitoring

### 3. Performance Optimization
- Implement caching for frequently accessed resources
- Use pagination for large datasets
- Stream large blobs instead of loading into memory

### 4. Security Guidelines
- Always authenticate MCP requests in production
- Implement rate limiting
- Sanitize file paths to prevent directory traversal
- Validate MIME types for uploads
- Encrypt sensitive data in blob storage

## Monitoring & Observability

### 1. Metrics to Track
- MCP request rate
- Resource access patterns
- Tool usage frequency
- Blob storage usage
- Error rates

### 2. Logging

```python
import logging
from app.core.logging import setup_mcp_logger

logger = setup_mcp_logger()

# Log MCP events
logger.info(f"MCP resource accessed: {resource_uri}")
logger.info(f"MCP tool called: {tool_name}")
logger.error(f"MCP error: {error_message}")
```

### 3. Health Checks

```python
@router.get("/mcp/health")
async def mcp_health():
    """MCP server health check."""
    return {
        "status": "healthy",
        "transport": settings.mcp_transport,
        "resources_available": True,
        "tools_available": True,
        "blob_storage_available": True
    }
```

## Conclusion

This MCP implementation provides PyFastStack with a powerful interface for AI agents to:

1. **Access structured data** from the database
2. **Manage blob storage** for files and media
3. **Interact with templates** and static assets
4. **Execute tools** for searching and analysis
5. **Maintain security** through proper authentication

The implementation follows MCP best practices and integrates seamlessly with PyFastStack's existing architecture, making your application AI-ready for the next generation of AI assistants and agents.