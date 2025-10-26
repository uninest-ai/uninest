#!/usr/bin/env python3
"""
Simple load testing script for the /metrics endpoint.

Sends multiple requests to generate traffic and then checks the metrics.
"""

import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configuration
BASE_URL = "http://localhost:8000"
TOTAL_REQUESTS = 500
CONCURRENT_WORKERS = 10


def send_request(request_num):
    """Send a single request to the root endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        return {
            "request_num": request_num,
            "status_code": response.status_code,
            "success": response.status_code == 200
        }
    except Exception as e:
        return {
            "request_num": request_num,
            "status_code": None,
            "success": False,
            "error": str(e)
        }


def main():
    print(f"🚀 Starting load test...")
    print(f"   Target: {BASE_URL}")
    print(f"   Total requests: {TOTAL_REQUESTS}")
    print(f"   Concurrent workers: {CONCURRENT_WORKERS}")
    print()

    # Send requests
    start_time = time.time()
    successful_requests = 0
    failed_requests = 0

    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [
            executor.submit(send_request, i)
            for i in range(TOTAL_REQUESTS)
        ]

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                successful_requests += 1
            else:
                failed_requests += 1

            # Progress indicator
            total = successful_requests + failed_requests
            if total % 50 == 0:
                print(f"   Progress: {total}/{TOTAL_REQUESTS} requests sent...")

    end_time = time.time()
    duration = end_time - start_time

    print()
    print(f"✅ Load test completed!")
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Successful: {successful_requests}")
    print(f"   Failed: {failed_requests}")
    print(f"   Throughput: {TOTAL_REQUESTS/duration:.2f} req/s")
    print()

    # Wait a moment for metrics to settle
    time.sleep(1)

    # Fetch metrics
    print("📊 Fetching metrics...")
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.json()
            print()
            print("=" * 50)
            print("METRICS REPORT")
            print("=" * 50)
            print(json.dumps(metrics, indent=2))
            print("=" * 50)
            print()
            print("Latency Percentiles (ms):")
            print(f"  P50 (median): {metrics['latency_ms']['p50']} ms")
            print(f"  P95: {metrics['latency_ms']['p95']} ms")
            print(f"  P99: {metrics['latency_ms']['p99']} ms")
            print()
            print(f"QPS (last 1 minute): {metrics['qps_1m']} req/s")
            print()
        else:
            print(f"❌ Failed to fetch metrics: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching metrics: {e}")


if __name__ == "__main__":
    main()