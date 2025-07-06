"""Gunicorn configuration file for PyFastStack."""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 4096  # Increased from 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 10000  # Increased from 1000
max_requests = 10000  # Increased from 1000
max_requests_jitter = 500  # Increased from 50
timeout = 120  # Increased from 30 seconds
graceful_timeout = 60  # Increased from 30 seconds
keepalive = 5  # Increased from 2 seconds

# Restart workers after this many requests, to help prevent memory leaks
max_requests_per_child = 10000  # Increased from 1000

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "pyfaststack"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment for HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Request limits
limit_request_line = 8192  # Maximum size of HTTP request line
limit_request_fields = 200  # Maximum number of header fields
limit_request_field_size = 8192  # Maximum size of header field

# Worker timeout
# Use /tmp on macOS since /dev/shm doesn't exist
import platform
if platform.system() == "Darwin":
    worker_tmp_dir = "/tmp"
else:
    worker_tmp_dir = "/dev/shm"

# Application preloading (saves memory but makes reload harder)
preload_app = False

# Enable automatic worker restarts on code changes in development
reload = os.environ.get("DEBUG", "").lower() == "true"
reload_engine = "auto"
reload_extra_files = []