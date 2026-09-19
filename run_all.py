#!/usr/bin/env python3
"""
TRU Community Test Suite — Unified Master Runner
Enables executing:
  ./run_all.py            -> Runs all test rounds sequentially
  ./run_all.py --round 1  -> Runs only Round 1 (Baseline Features)
  ./run_all.py --round 2  -> Runs only Round 2 (Core 0.05, VM Limits, Fuzzing)
"""

import os
import sys
import argparse
import subprocess
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

ROUNDS = {
    1: {
        "title": "Round 1 — Protocol Feature & Infrastructure Baseline",
        "dir": os.path.join(ROOT_DIR, "round_1"),
        "script": "run_round1.py"
    },
    2: {
        "title": "Round 2 — Core 0.05, VM Bounds, Malleability & P2P Fuzzing",
        "dir": os.path.join(ROOT_DIR, "round_2"),
        "script": "run_round2.py"
    }
}

def parse_args():
    parser = argparse.ArgumentParser(description="TRU Community Test Suite Master Runner")
    parser.add_argument("--round", "-r", type=int, choices=[1, 2], default=0,
                        help="Specific round to execute (1 or 2). Default: all rounds.")
    return parser.parse_args()

def execute_round(round_num: int) -> bool:
    info = ROUNDS[round_num]
    r_dir = info["dir"]
    r_script = info["script"]
    script_path = os.path.join(r_dir, r_script)
    
    print("\n" + "=" * 80)
    print(f"🚀 STARTING: {info['title']}")
    print("=" * 80)

    if not os.path.exists(script_path):
        print(f"[!] Error: Runner script not found at {script_path}")
        return False

    t0 = time.time()
    res = subprocess.run([sys.executable, r_script], cwd=r_dir)
    elapsed = time.time() - t0
    passed = (res.returncode == 0)
    
    status = "SUCCESS ✅" if passed else "FAILED ❌"
    print(f"\n[{status}] {info['title']} completed in {elapsed:.2f}s")
    return passed

def main():
    args = parse_args()
    t_start = time.time()
    
    rounds_to_run = [args.round] if args.round in ROUNDS else [1, 2]
    overall_status = {}

    print("=" * 80)
    print("💎 TOKENIZED REAL UTILITY (TRU) COMMUNITY TEST SUITE")
    print(f"🎯 Target Execution: {', '.join(f'Round {r}' for r in rounds_to_run)}")
    print("=" * 80)

    for r_num in rounds_to_run:
        passed = execute_round(r_num)
        overall_status[r_num] = passed

    total_time = time.time() - t_start
    print("\n" + "=" * 80)
    print("🏁 FINAL SUMMARY REPORT")
    print("=" * 80)
    all_passed = True
    for r_num, passed in overall_status.items():
        icon = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {icon} | Round {r_num}: {ROUNDS[r_num]['title']}")
        if not passed:
            all_passed = False

    print(f"\nTotal Suite Runtime: {total_time:.2f}s")
    if all_passed:
        print("🎉 ALL TEST SUITES PASSED FLAWLESSLY!")
        sys.exit(0)
    else:
        print("⚠️ SOME TEST SUITES ENCOUNTERED ERRORS.")
        sys.exit(1)

if __name__ == "__main__":
    main()
