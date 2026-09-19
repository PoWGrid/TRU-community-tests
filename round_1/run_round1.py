#!/usr/bin/env python3
"""
TRU Community Test Suite Master Runner
Executes all 6 feature tests requested by TRU Core Developer:
1. TRUSCRIPTIONS
2. Smart Contracts (TimeLock + Voting Gas Model)
3. Living Token Evolution (SFT KRAKEN Epoch 1 -> 2)
4. Web Wallet & Backups
5. Cross-Chain HTLC Swaps & Bridges
6. Mobile PWA & Browser Mining
"""

import os
import sys
import time
import subprocess
import json

TESTS = [
    ("01_truscriptions_test.py", "TRUSCRIPTIONS (On-Chain Inscriptions)"),
    ("02_smart_contracts_test.py", "Smart Contracts (TimeLock & Voting Gas Model)"),
    ("03_token_evolution_test.py", "Living Token Evolution (SFT KRAKEN Epoch 1 -> 2)"),
    ("04_web_wallet_backup_test.py", "Web Wallet & Backups (Client-Side Custody)"),
    ("05_swap_htlc_test.py", "Cross-Chain HTLC Swaps & Bridges (Reorg Safety)"),
    ("06_pwa_mobile_miner_test.py", "Mobile PWA & Browser Mining (WEB-MINER-01)")
]

def main():
    start_total = time.time()
    print("=" * 80)
    print("      TRU CORE PROTOCOL: OFFICIAL COMMUNITY FEATURE TEST SUITE")
    print("=" * 80)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"Directory: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Total Suites to Execute: {len(TESTS)}\n")

    results = []

    for filename, description in TESTS:
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        print(f"\n>>> Running: {description} [{filename}]")
        t0 = time.time()
        proc = subprocess.run([sys.executable, filepath], capture_output=False)
        elapsed = time.time() - t0

        status = "PASS" if proc.returncode == 0 else "FAIL"
        results.append({
            "script": filename,
            "description": description,
            "status": status,
            "exit_code": proc.returncode,
            "duration_sec": round(elapsed, 2)
        })

    total_duration = round(time.time() - start_total, 2)

    print("\n" + "=" * 80)
    print("                      TEST SUITE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"{'#':<3} | {'Test Description':<52} | {'Status':<6} | {'Time':<6}")
    print("-" * 80)

    all_passed = True
    for idx, r in enumerate(results, start=1):
        status_str = f"✅ {r['status']}" if r['status'] == "PASS" else f"❌ {r['status']}"
        if r['status'] != "PASS":
            all_passed = False
        print(f"{idx:<3} | {r['description']:<50} | {status_str:<6} | {r['duration_sec']}s")

    print("-" * 80)
    print(f"Overall Result: {'ALL TESTS PASSED (6/6)' if all_passed else 'SOME TESTS FAILED'}")
    print(f"Total Duration: {total_duration}s")
    print("=" * 80)

    summary_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "summary_results.json")
    with open(summary_file, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "all_passed": all_passed,
            "total_duration_sec": total_duration,
            "results": results
        }, f, indent=2)
    print(f"\nExecution summary saved to: {summary_file}")

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
