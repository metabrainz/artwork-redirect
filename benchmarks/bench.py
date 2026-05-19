#!/usr/bin/env python3
"""Benchmark artwork-redirect endpoints against a running server.

Usage:
    uv run benchmarks/bench.py [--host HOST] [--port PORT] [--iterations N]

Requires the server to be running. Does not follow redirects.
"""

import argparse
import http.client
import os
import signal
import subprocess
import sys
import time

ENDPOINTS = [
    ("/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/front", "release/front (hit)"),
    ("/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/back", "release/back (hit)"),
    ("/release/353710ec-1509-4df9-8ce2-9bd5011e3b80/", "release/index (hit)"),
    ("/release-group/67a63246-0de4-4cd8-8ce2-35f70a17f92b/front", "release-group/front"),
    ("/release/00000000-0000-0000-0000-000000000000/front", "release/front (404)"),
    ("/event/ebe6ce0f-22c0-4fe7-bfd4-7a0397c9fe94/front", "event/front (hit)"),
    ("/", "/ (index html)"),
    ("/robots.txt", "robots.txt"),
    ("/img/big_logo.svg", "img/big_logo.svg"),
]

WARMUP = 5


def bench_endpoint(host, port, path, iterations):
    conn = http.client.HTTPConnection(host, port)
    for _ in range(WARMUP):
        conn.request("GET", path, headers={"Host": "coverartarchive.org"})
        conn.getresponse().read()

    times = []
    codes = {}
    for _ in range(iterations):
        start = time.perf_counter()
        conn.request("GET", path, headers={"Host": "coverartarchive.org"})
        resp = conn.getresponse()
        resp.read()
        times.append(time.perf_counter() - start)
        codes[resp.status] = codes.get(resp.status, 0) + 1

    conn.close()
    avg = sum(times) / len(times) * 1000
    p50 = sorted(times)[len(times) // 2] * 1000
    p95 = sorted(times)[int(len(times) * 0.95)] * 1000
    codes_str = " ".join(f"{code}:{count * 100 // iterations}%" for code, count in sorted(codes.items()))
    return avg, p50, p95, codes_str


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--iterations", "-n", type=int, default=200)
    parser.add_argument("--serve", action="store_true", help="Auto-start and stop the server")
    args = parser.parse_args()

    server = None
    if args.serve:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        server = subprocess.Popen(
            [sys.executable, "artwork_redirect_server.py"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait for server to be ready
        for _ in range(20):
            try:
                conn = http.client.HTTPConnection(args.host, args.port, timeout=1)
                conn.request("GET", "/")
                conn.getresponse()
                conn.close()
                break
            except Exception:
                time.sleep(0.2)
        else:
            print("Server failed to start", file=sys.stderr)
            server.kill()
            sys.exit(1)

    try:
        print(f"Benchmarking {args.host}:{args.port} ({args.iterations} iterations)\n")
        print(f"{'Endpoint':<30} {'Avg (ms)':>10} {'P50 (ms)':>10} {'P95 (ms)':>10}  {'Codes'}")
        print("-" * 80)
        for path, label in ENDPOINTS:
            avg, p50, p95, codes_str = bench_endpoint(args.host, args.port, path, args.iterations)
            print(f"{label:<30} {avg:>10.2f} {p50:>10.2f} {p95:>10.2f}  {codes_str}")
    finally:
        if server:
            server.send_signal(signal.SIGTERM)
            server.wait()


if __name__ == "__main__":
    main()
