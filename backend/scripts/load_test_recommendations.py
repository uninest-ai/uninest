#!/usr/bin/env python3
"""
HTTP-based load test for recommendations endpoint.

Measures performance via /metrics endpoint after generating traffic.
No database access needed - works via HTTP API only.

Usage:
    # 1. Start the backend server
    docker-compose up -d

    # 2. Get your auth token (login first)
    export AUTH_TOKEN="your_jwt_token_here"

    # 3. Run the load test
    python scripts/load_test_recommendations.py
"""

import requests
import time
import json
import statistics
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")  # Set this to your JWT token
TOTAL_REQUESTS = 200
CONCURRENT_WORKERS = 10


def send_recommendation_request(request_num: int, token: str):
    """Send a request to the recommendations endpoint."""
    try:
        start = time.perf_counter()
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        response = requests.get(
            f"{BASE_URL}/recommendations/properties?limit=10",
            headers=headers,
            timeout=10
        )

        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "request_num": request_num,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "success": response.status_code == 200
        }
    except Exception as e:
        return {
            "request_num": request_num,
            "status_code": None,
            "latency_ms": None,
            "success": False,
            "error": str(e)
        }


def main():
    print("=" * 70)
    print("🚀 RECOMMENDATIONS ENDPOINT LOAD TEST")
    print("=" * 70)
    print(f"   Target: {BASE_URL}/recommendations/properties")
    print(f"   Total requests: {TOTAL_REQUESTS}")
    print(f"   Concurrent workers: {CONCURRENT_WORKERS}")

    if not AUTH_TOKEN:
        print("\n⚠️  WARNING: No AUTH_TOKEN set. Requests will fail if authentication required.")
        print("   Set token with: export AUTH_TOKEN='your_jwt_token'")
        response = input("\n   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    print("\n🔥 Starting load test...\n")

    # Send requests
    start_time = time.time()
    successful_requests = 0
    failed_requests = 0
    latencies = []

    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [
            executor.submit(send_recommendation_request, i, AUTH_TOKEN)
            for i in range(TOTAL_REQUESTS)
        ]

        for future in as_completed(futures):
            result = future.result()

            if result["success"]:
                successful_requests += 1
                if result["latency_ms"]:
                    latencies.append(result["latency_ms"])
            else:
                failed_requests += 1
                if failed_requests <= 3:  # Show first 3 errors
                    print(f"   ❌ Error: {result.get('error', f'HTTP {result.get('status_code')}')}")

            # Progress indicator
            total = successful_requests + failed_requests
            if total % 20 == 0:
                print(f"   Progress: {total}/{TOTAL_REQUESTS} requests sent...")

    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "=" * 70)
    print("✅ LOAD TEST COMPLETED")
    print("=" * 70)
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Successful: {successful_requests}")
    print(f"   Failed: {failed_requests}")
    print(f"   Throughput: {TOTAL_REQUESTS/duration:.2f} req/s")

    # Calculate client-side latencies
    if latencies:
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        print(f"\n📊 CLIENT-SIDE LATENCIES:")
        print(f"   Mean: {statistics.mean(latencies):.1f} ms")
        print(f"   Median: {statistics.median(latencies):.1f} ms")
        print(f"   p95: {sorted_latencies[int(0.95 * (n-1))]:.1f} ms")
        print(f"   p99: {sorted_latencies[int(0.99 * (n-1))]:.1f} ms")

    # Wait for metrics to settle
    time.sleep(2)

    # Fetch server-side metrics
    print("\n📈 Fetching server metrics from /metrics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.json()

            print("\n" + "=" * 70)
            print("📊 SERVER-SIDE METRICS (/metrics endpoint)")
            print("=" * 70)
            print(f"\n   Latency Percentiles (ms):")
            print(f"      p50 (median): {metrics['latency_ms']['p50']} ms")
            print(f"      p95: {metrics['latency_ms']['p95']} ms")
            print(f"      p99: {metrics['latency_ms']['p99']} ms")
            print(f"\n   QPS (last 1 minute): {metrics['qps_1m']} req/s")

            # Save results
            results = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "load_test": {
                    "total_requests": TOTAL_REQUESTS,
                    "successful": successful_requests,
                    "failed": failed_requests,
                    "duration_sec": round(duration, 2),
                    "throughput_qps": round(TOTAL_REQUESTS/duration, 2)
                },
                "server_metrics": metrics
            }

            output_file = "load_test_results.json"
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)

            print(f"\n💾 Results saved to: {output_file}")

            # Generate resume snippet
            print("\n" + "=" * 70)
            print("📝 METRICS FOR RESUME:")
            print("=" * 70)
            print(f"   QPS: ~{metrics['qps_1m']} req/s")
            print(f"   p95 latency: ~{metrics['latency_ms']['p95']} ms")
            print(f"   p99 latency: ~{metrics['latency_ms']['p99']} ms")

        else:
            print(f"   ❌ Failed to fetch metrics: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error fetching metrics: {e}")


if __name__ == "__main__":
    main()