#!/usr/bin/env python
"""
Load testing script to test increased request limits.
Created by George Khananaev
https://george.khananaev.com/
"""

import asyncio
import aiohttp
import time
import sys
from colorama import init, Fore, Style

init(autoreset=True)

async def test_endpoint(session, url):
    """Test a single request."""
    try:
        start = time.time()
        async with session.get(url) as response:
            await response.text()
            return time.time() - start, response.status
    except Exception as e:
        return None, str(e)

async def load_test(url, num_requests, concurrent):
    """Run load test with specified concurrency."""
    print(f"{Fore.CYAN}🚀 Starting load test...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}URL: {url}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Total Requests: {num_requests}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Concurrent Requests: {concurrent}{Style.RESET_ALL}")
    print()
    
    connector = aiohttp.TCPConnector(limit=concurrent, limit_per_host=concurrent)
    timeout = aiohttp.ClientTimeout(total=120)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        start_time = time.time()
        
        # Create all tasks
        tasks = []
        for i in range(num_requests):
            task = test_endpoint(session, url)
            tasks.append(task)
            
            # Limit concurrency
            if len(tasks) >= concurrent:
                results = await asyncio.gather(*tasks)
                tasks = []
                
                # Progress indicator
                completed = i + 1
                if completed % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    print(f"{Fore.GREEN}Progress: {completed}/{num_requests} "
                          f"({rate:.1f} req/s){Style.RESET_ALL}")
        
        # Handle remaining tasks
        if tasks:
            await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
    
    # Print results
    print()
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ Load Test Complete!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Total Time: {total_time:.2f} seconds{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Requests/second: {num_requests/total_time:.2f}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Avg Response Time: {total_time/num_requests*1000:.2f} ms{Style.RESET_ALL}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print(f"{Fore.RED}Usage: python load_test.py <url> [requests] [concurrent]{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Example: python load_test.py http://localhost:8000/health 10000 100{Style.RESET_ALL}")
        sys.exit(1)
    
    url = sys.argv[1]
    num_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    concurrent = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    # Run the test
    asyncio.run(load_test(url, num_requests, concurrent))

if __name__ == "__main__":
    main()