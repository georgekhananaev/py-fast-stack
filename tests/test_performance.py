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
        start_time = time.time()
        response = await client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"\nSingle request response time: {response_time:.2f}ms")
        assert response_time < 100  # Should respond in less than 100ms
    
    @pytest.mark.asyncio
    async def test_concurrent_health_requests(self, client: AsyncClient):
        """Test concurrent requests to health endpoint."""
        num_requests = 100
        
        async def make_request() -> float:
            start_time = time.time()
            response = await client.get("/health")
            end_time = time.time()
            assert response.status_code == 200
            return (end_time - start_time) * 1000
        
        start_time = time.time()
        tasks = [make_request() for _ in range(num_requests)]
        response_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        requests_per_second = num_requests / total_time
        
        print(f"\n--- Concurrent Health Endpoint Test ---")
        print(f"Total requests: {num_requests}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Requests/second: {requests_per_second:.2f}")
        print(f"Avg response time: {avg_response_time:.2f}ms")
        print(f"Min response time: {min_response_time:.2f}ms")
        print(f"Max response time: {max_response_time:.2f}ms")
        
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
        num_iterations = 10
        concurrent_users = 5
        
        async def user_scenario() -> Tuple[str, float]:
            """Simulate a user scenario."""
            results = []
            
            # 1. Health check
            start = time.time()
            response = await client.get("/health")
            assert response.status_code == 200
            results.append(("health", (time.time() - start) * 1000))
            
            # 2. Register
            start = time.time()
            # Use timestamp + random to ensure uniqueness
            timestamp = int(time.time() * 1000000)
            rand_num = random.randint(1000, 9999)
            user_id = f"{timestamp}_{rand_num}"
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"perf{user_id}@example.com",
                    "username": f"perfuser{user_id}",
                    "password": "perfpass123",
                    "full_name": "Performance Test User"
                }
            )
            assert response.status_code == 200
            results.append(("register", (time.time() - start) * 1000))
            
            # 3. Login
            start = time.time()
            response = await client.post(
                "/api/v1/auth/login",
                data={
                    "username": f"perfuser{user_id}",
                    "password": "perfpass123"
                }
            )
            assert response.status_code == 200
            token = response.json()["access_token"]
            results.append(("login", (time.time() - start) * 1000))
            
            # 4. Get profile
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
        
        total_time = time.time() - start_time
        
        # Analyze results
        endpoint_stats = {}
        for user_results in all_results:
            for endpoint, response_time in user_results:
                if endpoint not in endpoint_stats:
                    endpoint_stats[endpoint] = []
                endpoint_stats[endpoint].append(response_time)
        
        print(f"\nTotal test time: {total_time:.2f}s")
        print(f"Total requests: {len(all_results) * 4}")
        print(f"Overall requests/second: {(len(all_results) * 4) / total_time:.2f}")
        
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
        """Stress test the health endpoint with high load."""
        duration_seconds = 5
        print(f"\n--- Stress Test: Health Endpoint ---")
        print(f"Duration: {duration_seconds} seconds")
        print("Testing maximum requests/second...")
        
        request_count = 0
        error_count = 0
        response_times = []
        start_time = time.time()
        
        async def continuous_requests():
            nonlocal request_count, error_count
            while time.time() - start_time < duration_seconds:
                try:
                    req_start = time.time()
                    response = await client.get("/health")
                    req_time = (time.time() - req_start) * 1000
                    
                    if response.status_code == 200:
                        request_count += 1
                        response_times.append(req_time)
                    else:
                        error_count += 1
                except Exception:
                    error_count += 1
        
        # Run multiple concurrent workers
        workers = 10
        tasks = [continuous_requests() for _ in range(workers)]
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        requests_per_second = request_count / total_time
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        print(f"\nResults:")
        print(f"Total requests: {request_count}")
        print(f"Failed requests: {error_count}")
        print(f"Success rate: {(request_count / (request_count + error_count) * 100):.1f}%")
        print(f"Requests/second: {requests_per_second:.2f}")
        print(f"Avg response time: {avg_response_time:.2f}ms")
        print(f"95th percentile: {p95_response_time:.2f}ms")
        print(f"99th percentile: {p99_response_time:.2f}ms")
        
        assert requests_per_second > 100  # Should handle at least 100 req/s
        assert error_count / (request_count + error_count) < 0.01  # Less than 1% errors