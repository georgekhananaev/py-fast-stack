#!/usr/bin/env python
"""
Run tests in batches to avoid rate limiting.
"""
import subprocess
import time
import sys

# Define test groups that can run together without hitting rate limits
# Groups are designed to run tests that don't conflict with rate limits
TEST_GROUPS = [
    # Health and performance tests (no rate limits)
    [
        "tests/test_auth.py::TestHealthCheck",
        "tests/test_performance.py::TestPerformance::test_health_endpoint_single_request",
        "tests/test_performance.py::TestPerformance::test_stress_test_health_endpoint",
        "tests/test_rate_limiter.py::test_health_endpoint_not_rate_limited",
    ],
    
    # Basic auth tests (uses pre-created users)
    [
        "tests/test_auth.py::TestAuthentication::test_get_current_user",
        "tests/test_auth.py::TestAuthentication::test_get_current_user_no_token",
        "tests/test_auth.py::TestAuthentication::test_get_current_user_invalid_token",
    ],
    
    # User operations tests
    [
        "tests/test_users.py::TestUserOperations::test_list_users_as_superuser",
        "tests/test_users.py::TestUserOperations::test_list_users_as_regular_user",
        "tests/test_users.py::TestUserOperations::test_get_user_by_id",
        "tests/test_users.py::TestUserOperations::test_get_nonexistent_user",
    ],
    
    # User update tests
    [
        "tests/test_users.py::TestUserOperations::test_update_user_as_superuser",
        "tests/test_users.py::TestUserOperations::test_update_user_as_regular_user",
    ],
    
    # Web user operations tests
    [
        "tests/test_users_web.py::TestWebUserOperations::test_dashboard_access",
        "tests/test_users_web.py::TestWebUserOperations::test_dashboard_redirect_without_auth",
        "tests/test_users_web.py::TestWebUserOperations::test_profile_update",
    ],
    
    # Web admin tests
    [
        "tests/test_users_web.py::TestWebUserOperations::test_admin_user_management_access",
        "tests/test_users_web.py::TestWebUserOperations::test_admin_user_management_regular_user_denied",
    ],
    
    # Registration tests (creates new users)
    [
        "tests/test_auth.py::TestAuthentication::test_register_user",
        "tests/test_auth.py::TestAuthentication::test_register_duplicate_email",
        "tests/test_auth.py::TestAuthentication::test_register_duplicate_username",
    ],
    
    # Login tests
    [
        "tests/test_auth.py::TestAuthentication::test_login_success",
        "tests/test_auth.py::TestAuthentication::test_login_wrong_password",
        "tests/test_auth.py::TestAuthentication::test_login_nonexistent_user",
    ],
    
    # Special tests
    [
        "tests/test_auth.py::TestAuthentication::test_login_inactive_user",
        "tests/test_users_web.py::TestWebUserOperations::test_delete_user_protection",
        "tests/test_users_web.py::TestWebUserOperations::test_self_deletion_protection",
    ],
    
    # Password change tests
    [
        "tests/test_users_web.py::TestWebUserOperations::test_password_change",
        "tests/test_users_web.py::TestWebUserOperations::test_password_change_wrong_current_password",
        "tests/test_users_web.py::TestWebUserOperations::test_password_change_mismatch",
    ],
    
    # Performance tests that might create users
    [
        "tests/test_performance.py::TestPerformance::test_authenticated_endpoint_performance",
        "tests/test_performance.py::TestPerformance::test_database_operation_performance",
    ],
    
    # Concurrent tests (run separately)
    [
        "tests/test_performance.py::TestPerformance::test_concurrent_health_requests",
    ],
    
    # Load test (creates many users)
    [
        "tests/test_performance.py::TestPerformance::test_load_test_mixed_endpoints",
    ],
]

# Rate limit tests should be run separately with enough time between them
RATE_LIMIT_TESTS = [
    "tests/test_rate_limiter.py::test_login_rate_limit",
    "tests/test_rate_limiter.py::test_register_rate_limit",
    "tests/test_rate_limiter.py::test_web_login_rate_limit",
    "tests/test_rate_limiter.py::test_web_register_rate_limit",
    "tests/test_rate_limiter.py::test_newsletter_subscription_rate_limit",
    "tests/test_rate_limiter.py::test_rate_limit_resets_after_time",
]


def run_test_group(tests, group_name=""):
    """Run a group of tests."""
    if group_name:
        print(f"\n{'='*60}")
        print(f"Running {group_name}")
        print(f"{'='*60}")
    
    cmd = ["python", "-m", "pytest", "-v", "--tb=short"] + tests
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    """Run all tests in groups with delays to avoid rate limiting."""
    print("Setting up test environment...")
    
    # First, create test users
    print("\nCreating test users...")
    subprocess.run(["python", "tests/create_test_users.py"])
    
    # Run regular test groups
    failed_groups = []
    for i, group in enumerate(TEST_GROUPS):
        group_name = f"Test Group {i+1}/{len(TEST_GROUPS)}"
        returncode = run_test_group(group, group_name)
        if returncode != 0:
            failed_groups.append(group_name)
        
        # Delay between groups to avoid rate limiting
        if i < len(TEST_GROUPS) - 1:
            print(f"\nWaiting 10 seconds before next group...")
            time.sleep(10)
    
    # Wait before running rate limit tests
    print("\nWaiting 65 seconds before running rate limit tests...")
    time.sleep(65)
    
    # Run rate limit tests one by one
    print("\n" + "="*60)
    print("Running Rate Limit Tests")
    print("="*60)
    
    for i, test in enumerate(RATE_LIMIT_TESTS):
        print(f"\nRunning rate limit test {i+1}/{len(RATE_LIMIT_TESTS)}: {test}")
        returncode = run_test_group([test])
        if returncode != 0:
            failed_groups.append(f"Rate limit test: {test}")
        
        # Wait between rate limit tests
        if i < len(RATE_LIMIT_TESTS) - 1:
            print("Waiting 65 seconds before next rate limit test...")
            time.sleep(65)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if failed_groups:
        print(f"\n❌ {len(failed_groups)} test groups failed:")
        for group in failed_groups:
            print(f"  - {group}")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()