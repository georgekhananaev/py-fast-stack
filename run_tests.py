#!/usr/bin/env python
"""
Test runner script for PyFastStack.
Created by George Khananaev
https://george.khananaev.com/
"""

import subprocess
import sys
import time
import requests
from colorama import init, Fore, Style

init(autoreset=True)

def check_server():
    """Check if the server is running."""
    try:
        response = requests.get("http://localhost:8000/health")
        return response.status_code == 200
    except:
        return False

def main():
    """Run the tests with server check."""
    print(f"{Fore.CYAN}🧪 PyFastStack Test Runner{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Created by George Khananaev{Style.RESET_ALL}")
    print(f"{Fore.CYAN}https://george.khananaev.com/{Style.RESET_ALL}")
    print()
    
    # Check if server is running
    print(f"{Fore.YELLOW}Checking if server is running...{Style.RESET_ALL}")
    if not check_server():
        print(f"{Fore.RED}❌ Server is not running!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please start the server first:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}uv run python run.py{Style.RESET_ALL}")
        print()
        print(f"{Fore.YELLOW}Then run tests in another terminal:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}uv run python run_tests.py{Style.RESET_ALL}")
        sys.exit(1)
    
    print(f"{Fore.GREEN}✅ Server is running!{Style.RESET_ALL}")
    print()
    
    # Get test arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Default to verbose if no args provided
    if not args:
        args = ["-v"]
    
    # Run pytest
    print(f"{Fore.YELLOW}Running tests...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    
    cmd = ["uv", "run", "pytest"] + args
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ All tests passed!{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.RED}❌ Some tests failed.{Style.RESET_ALL}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())