#!/usr/bin/env python
"""
Run the PyFastStack application.
Created by George Khananaev
https://george.khananaev.com/
"""

import sys
import subprocess
import asyncio
from colorama import init, Fore, Style
from app.core.config import get_settings
from app.db.init_db import run_init

# Initialize colorama for colored output
init(autoreset=True)

settings = get_settings()


def run_dev():
    """Run in development mode with hot reload."""
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "app.main:app",
        "-c",
        "gunicorn.conf.py",
        "--reload",
        "--log-level",
        "debug",
        "--workers",
        "1",  # Single worker for development
    ]
    subprocess.run(cmd)


def run_prod():
    """Run in production mode with Gunicorn."""
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "app.main:app",
        "-c",
        "gunicorn.conf.py",
    ]
    subprocess.run(cmd)


async def initialize_database():
    """Initialize database and create root user."""
    print(f"{Fore.CYAN}🗄️  Initializing database...{Style.RESET_ALL}")
    
    result = await run_init()
    
    if result["created"]:
        print(f"\n{Fore.GREEN}✅ Database initialized successfully!{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🔐 ROOT USER CREDENTIALS{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Username: {Fore.WHITE}{result['username']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Password: {Fore.WHITE}{result['password']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Email:    {Fore.WHITE}{result['email']}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.RED}⚠️  Please save these credentials securely!{Style.RESET_ALL}")
        print(f"{Fore.RED}⚠️  The password will not be shown again!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*50}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.BLUE}ℹ️  Database already initialized. Root user exists.{Style.RESET_ALL}")


if __name__ == "__main__":
    # Initialize database first
    asyncio.run(initialize_database())
    
    if settings.debug:
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}PyFastStack v1.0.0 - Created by George Khananaev{Style.RESET_ALL}")
        print(f"{Fore.CYAN}https://george.khananaev.com/{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}🚀 Starting PyFastStack in development mode...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📝 API Documentation: {Fore.WHITE}http://localhost:8000/docs{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🌐 Web Interface: {Fore.WHITE}http://localhost:8000{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🔄 Hot reload is enabled{Style.RESET_ALL}\n")
        run_dev()
    else:
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}PyFastStack v1.0.0 - Created by George Khananaev{Style.RESET_ALL}")
        print(f"{Fore.CYAN}https://george.khananaev.com/{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}🚀 Starting PyFastStack in production mode...{Style.RESET_ALL}")
        run_prod()