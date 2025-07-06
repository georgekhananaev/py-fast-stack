#!/usr/bin/env python
"""
Clean up temporary files and directories.
Created by George Khananaev
https://george.khananaev.com/
"""

import os
import shutil
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

def clean_project():
    """Clean up temporary files and directories."""
    print(f"{Fore.CYAN}🧹 Cleaning up PyFastStack project...{Style.RESET_ALL}\n")
    
    # Patterns to remove
    patterns_to_remove = [
        # Python cache
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/*$py.class",
        
        # Logs
        "*.log",
        "*.log.*",
        "server.log",
        "nohup.out",
        
        # Databases
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "test.db",
        "pyfaststack.db",
        
        # Temporary files
        "*.tmp",
        "*.temp",
        "*.bak",
        "*.cache",
        "*.pid",
        "*.sock",
        
        # Test coverage
        ".coverage",
        "htmlcov/",
        ".pytest_cache/",
        
        # IDE
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        
        # Credentials (should never be committed)
        "admin_credentials.txt",
        "credentials.txt",
        
        # OS files
        ".DS_Store",
        "Thumbs.db",
    ]
    
    removed_count = 0
    
    for pattern in patterns_to_remove:
        # Handle glob patterns
        if "**" in pattern or "*" in pattern:
            for path in Path(".").rglob(pattern.replace("**/", "")):
                if ".venv" not in str(path) and ".git" not in str(path):
                    try:
                        if path.is_dir():
                            shutil.rmtree(path)
                            print(f"{Fore.RED}Removed directory: {path}{Style.RESET_ALL}")
                        else:
                            path.unlink()
                            print(f"{Fore.YELLOW}Removed file: {path}{Style.RESET_ALL}")
                        removed_count += 1
                    except Exception as e:
                        print(f"{Fore.RED}Error removing {path}: {e}{Style.RESET_ALL}")
        else:
            # Handle specific files
            path = Path(pattern)
            if path.exists():
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                        print(f"{Fore.RED}Removed directory: {path}{Style.RESET_ALL}")
                    else:
                        path.unlink()
                        print(f"{Fore.YELLOW}Removed file: {path}{Style.RESET_ALL}")
                    removed_count += 1
                except Exception as e:
                    print(f"{Fore.RED}Error removing {path}: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}✅ Cleanup complete! Removed {removed_count} items.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Your project is now clean!{Style.RESET_ALL}")

if __name__ == "__main__":
    clean_project()