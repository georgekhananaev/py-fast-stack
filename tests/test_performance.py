"""
Performance and load testing.
Created by George Khananaev
https://george.khananaev.com/
"""

import asyncio
import time
import random
from typing import List, Tuple
import pytest
from httpx import AsyncClient
import statistics


class TestPerformance:
    """Performance and load testing."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_single_request(self, client: AsyncClient):
        """Test single health endpoint request performance."""
        # Warm up the connection
        await client.get("/health")
        
        # Measure actual request
        start_time = time.time()
        response = await client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"\nSingle request response time: {response_time:.2f}ms")
        assert response_time < 100  # Should respond in less than 100ms
    
    @pytest.mark.asyncio
    async def test_concurrent_health_requests(self, client: AsyncClient):
        """Test concurrent requests to health endpoint to measure real throughput."""
        num_requests = 500  # Reasonable number for testing
        concurrent_workers = 20  # Reduced concurrent connections
        
        async def make_request() -> float:
            start_time = time.time()
            response = await client.get("/health")
            end_time = time.time()
            assert response.status_code == 200
            return (end_time - start_time) * 1000
        
        # Warm up
        await asyncio.gather(*[client.get("/health") for _ in range(10)])
        
        print(f"\n--- Concurrent Health Endpoint Performance Test ---")
        print(f"Testing with {concurrent_workers} concurrent connections")
        
        start_time = time.time()
        tasks = [make_request() for _ in range(num_requests)]
        response_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        requests_per_second = num_requests / total_time
        
        print(f"Total requests: {num_requests}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests/second: {requests_per_second:.2f}")
        print(f"Avg response time: {avg_response_time:.2f}ms")
        print(f"Median response time: {median_response_time:.2f}ms")
        print(f"Min response time: {min_response_time:.2f}ms")
        print(f"Max response time: {max_response_time:.2f}ms")
        print(f"95th percentile: {p95_response_time:.2f}ms")
        print(f"99th percentile: {p99_response_time:.2f}ms")
        
        # This shows the real capability of the server
        print(f"\nThe server can handle approximately {requests_per_second:.0f} requests/second for the health endpoint")
        
        assert requests_per_second > 50  # Should handle at least 50 req/s
    
    @pytest.mark.asyncio
    async def test_authenticated_endpoint_performance(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test performance of authenticated endpoints."""
        num_requests = 50
        
        async def make_request() -> float:
            start_time = time.time()
            response = await client.get("/api/v1/auth/me", headers=auth_headers)
            end_time = time.time()
            assert response.status_code == 200
            return (end_time - start_time) * 1000
        
        start_time = time.time()
        tasks = [make_request() for _ in range(num_requests)]
        response_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        avg_response_time = statistics.mean(response_times)
        requests_per_second = num_requests / total_time
        
        print(f"\n--- Authenticated Endpoint Performance ---")
        print(f"Total requests: {num_requests}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests/second: {requests_per_second:.2f}")
        print(f"Avg response time: {avg_response_time:.2f}ms")
        
        assert avg_response_time < 200  # Auth endpoints should respond < 200ms
    
    @pytest.mark.asyncio
    async def test_database_operation_performance(
        self, client: AsyncClient, superuser_auth_headers: dict
    ):
        """Test performance of database operations."""
        num_requests = 20
        
        async def list_users() -> float:
            start_time = time.time()
            response = await client.get(
                "/api/v1/users/", 
                headers=superuser_auth_headers
            )
            end_time = time.time()
            assert response.status_code == 200
            return (end_time - start_time) * 1000
        
        response_times = []
        for _ in range(num_requests):
            response_time = await list_users()
            response_times.append(response_time)
        
        avg_response_time = statistics.mean(response_times)
        
        print(f"\n--- Database Operation Performance ---")
        print(f"Operation: List Users")
        print(f"Total requests: {num_requests}")
        print(f"Avg response time: {avg_response_time:.2f}ms")
        
        assert avg_response_time < 500  # DB operations should be < 500ms
    
    @pytest.mark.asyncio
    async def test_load_test_mixed_endpoints(self, client: AsyncClient):
        """Load test with mixed endpoint requests."""
        num_iterations = 5  # Reduced iterations
        concurrent_users = 1  # Run sequentially to avoid rate limiting
        
        # Use a shared counter to assign different test users
        user_counter = 0
        counter_lock = asyncio.Lock()
        
        async def user_scenario() -> Tuple[str, float]:
            """Simulate a user scenario."""
            nonlocal user_counter
            
            # Get a unique test user index
            async with counter_lock:
                user_idx = user_counter % 20  # We have 20 test users
                user_counter += 1
            
            results = []
            
            # 1. Health check
            start = time.time()
            response = await client.get("/health")
            assert response.status_code == 200
            results.append(("health", (time.time() - start) * 1000))
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(1)
            
            # 2. Login with pre-created test user
            start = time.time()
            username = f"testuser_{user_idx}"
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": username,
                    "password": "TestPassword123!"
                }
            )
            assert response.status_code == 200
            token = response.json()["access_token"]
            results.append(("login", (time.time() - start) * 1000))
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(1)
            
            # 3. Get profile
            start = time.time()
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            results.append(("profile", (time.time() - start) * 1000))
            
            return results
        
        print(f"\n--- Load Test: Mixed Endpoints ---")
        print(f"Concurrent users: {concurrent_users}")
        print(f"Iterations per user: {num_iterations}")
        
        all_results = []
        start_time = time.time()
        
        for i in range(num_iterations):
            tasks = [user_scenario() for _ in range(concurrent_users)]
            iteration_results = await asyncio.gather(*tasks)
            all_results.extend(iteration_results)
            
            if (i + 1) % 5 == 0:
                print(f"Completed {i + 1}/{num_iterations} iterations")
            
            # Add delay between iterations to avoid rate limiting
            await asyncio.sleep(2)
        
        total_time = time.time() - start_time
        
        # Analyze results
        endpoint_stats = {}
        for user_results in all_results:
            for endpoint, response_time in user_results:
                if endpoint not in endpoint_stats:
                    endpoint_stats[endpoint] = []
                endpoint_stats[endpoint].append(response_time)
        
        print(f"\nTotal test time: {total_time:.2f}s")
        print(f"Total requests: {len(all_results) * 3}")
        print(f"Overall requests/second: {(len(all_results) * 3) / total_time:.2f}")
        
        print("\nEndpoint Statistics:")
        for endpoint, times in endpoint_stats.items():
            avg_time = statistics.mean(times)
            max_time = max(times)
            min_time = min(times)
            print(f"\n{endpoint.upper()}:")
            print(f"  Avg: {avg_time:.2f}ms")
            print(f"  Min: {min_time:.2f}ms")
            print(f"  Max: {max_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_stress_test_health_endpoint(self, client: AsyncClient):
        """Stress test the health endpoint with high load to measure real server capacity."""
        duration_seconds = 10
        workers = 20  # Increased workers for better load testing
        
        print(f"\n--- Stress Test: Health Endpoint (Real Server Capacity) ---")
        print(f"Duration: {duration_seconds} seconds")
        print(f"Concurrent workers: {workers}")
        print("Testing maximum requests/second the server can handle...")
        
        request_count = 0
        error_count = 0
        response_times = []
        start_time = time.time()
        
        async def continuous_requests():
            nonlocal request_count, error_count
            local_count = 0
            while time.time() - start_time < duration_seconds:
                try:
                    req_start = time.time()
                    response = await client.get("/health")
                    req_time = (time.time() - req_start) * 1000
                    
                    if response.status_code == 200:
                        request_count += 1
                        local_count += 1
                        response_times.append(req_time)
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error: {e}")
            return local_count
        
        # Warm up
        await asyncio.gather(*[client.get("/health") for _ in range(10)])
        
        # Run stress test
        tasks = [continuous_requests() for _ in range(workers)]
        worker_counts = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        requests_per_second = request_count / total_time
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
        
        print(f"\nResults:")
        print(f"Total requests: {request_count}")
        print(f"Failed requests: {error_count}")
        print(f"Success rate: {(request_count / (request_count + error_count) * 100) if (request_count + error_count) > 0 else 0:.1f}%")
        print(f"Actual test duration: {total_time:.2f}s")
        print(f"\nThroughput:")
        print(f"  Requests/second: {requests_per_second:.2f}")
        print(f"  Requests/worker/second: {requests_per_second / workers:.2f}")
        print(f"\nResponse times:")
        print(f"  Average: {avg_response_time:.2f}ms")
        print(f"  Median: {median_response_time:.2f}ms")
        print(f"  95th percentile: {p95_response_time:.2f}ms")
        print(f"  99th percentile: {p99_response_time:.2f}ms")
        print(f"\nWorker statistics:")
        print(f"  Min requests per worker: {min(worker_counts)}")
        print(f"  Max requests per worker: {max(worker_counts)}")
        print(f"  Avg requests per worker: {sum(worker_counts) / len(worker_counts):.0f}")
        
        print(f"\n🚀 The server can handle approximately {requests_per_second:.0f} requests/second")
        print(f"   for the /health endpoint with {workers} concurrent connections")
        
        assert requests_per_second > 100  # Should handle at least 100 req/s
        assert error_count / (request_count + error_count) < 0.01 if (request_count + error_count) > 0 else True  # Less than 1% errors