#!/usr/bin/env python3
"""
TRU Community Test #05: CROSS-CHAIN HTLC SWAPS & BRIDGES
Tests cross-chain Hash Time Locked Contracts (HTLC) and reorg safety:
1. Canonical HTLC cryptographic preimage, Hash160, and dual-branch script generation.
2. Verification of node security guard: requireTruSwapRpcAuth (TRU_SWAP_RPC_TOKEN).
3. Execution of official TRU Swap regression test suites:
   - swap/reorg_swap_01c_selftest.py (15 regression tests, 5 explicit states)
   - swap/reorg_exit_01c_selftest.py (execution gate, duplicate protection)
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from common import (
    rpc_call,
    KRAKEN_ADDRESS,
    KRAKEN_PRIVKEY_HEX,
    privkey_to_pubkey,
    print_banner
)

def build_htlc_script(claim_pubkey_hex: str, refund_pubkey_hex: str,
                      secret_hash160_hex: str, lock_time: int) -> tuple[bytes, str]:
    # Canonical Bitcoin / TRU HTLC format:
    # OP_IF (0x63)
    #   OP_HASH160 (0xa9) 0x14 <secret_hash160> OP_EQUALVERIFY (0x88)
    #   0x21 <claim_pubkey> OP_CHECKSIG (0xac)
    # OP_ELSE (0x67)
    #   0x04 <lock_time> OP_CHECKLOCKTIMEVERIFY (0xb1) OP_DROP (0x75)
    #   0x21 <refund_pubkey> OP_CHECKSIG (0xac)
    # OP_ENDIF (0x68)
    h_bytes = bytes.fromhex(secret_hash160_hex)
    c_pub = bytes.fromhex(claim_pubkey_hex)
    r_pub = bytes.fromhex(refund_pubkey_hex)
    t_bytes = lock_time.to_bytes(4, 'little')

    script = (
        b'\x63' +
        b'\xa9\x14' + h_bytes + b'\x88' +
        bytes([len(c_pub)]) + c_pub + b'\xac' +
        b'\x67' +
        b'\x04' + t_bytes + b'\xb1\x75' +
        bytes([len(r_pub)]) + r_pub + b'\xac' +
        b'\x68'
    )
    return script, script.hex()

def run_test():
    print_banner("05 - CROSS-CHAIN HTLC SWAPS & BRIDGES (REORG RESILIENCE)")

    # 1. Cryptographic HTLC Preimage & Script Construction
    print("[*] 1. Generating Cryptographic HTLC Preimage and Script...")
    secret_bytes = os.urandom(32)
    secret_hex = secret_bytes.hex()
    sha_hash = hashlib.sha256(secret_bytes).digest()
    secret_hash160 = hashlib.new('ripemd160', sha_hash).hexdigest()

    _, kraken_pub_hex = privkey_to_pubkey(KRAKEN_PRIVKEY_HEX)
    # Counterparty mock pubkey for BSTY / BTC bridge
    counterparty_pub_hex = "03" + "11" * 32
    refund_lock_time = int(time.time()) + 7200  # 2 hours

    htlc_bytes, htlc_hex = build_htlc_script(
        claim_pubkey_hex=counterparty_pub_hex,
        refund_pubkey_hex=kraken_pub_hex,
        secret_hash160_hex=secret_hash160,
        lock_time=refund_lock_time
    )

    print(f"    [+] Secret Preimage (32 bytes): {secret_hex[:32]}...")
    print(f"    [+] Secret Hash160 (20 bytes):  {secret_hash160}")
    print(f"    [+] Refund Lock Time (CLTV):    {refund_lock_time}")
    print(f"    [+] Canonical HTLC Script:      {htlc_hex[:48]}... ({len(htlc_hex)//2} bytes)")

    # 2. Node RPC Security Guard Verification
    print("\n[*] 2. Verifying Core Node RPC Security Guard (TRU_SWAP_RPC_TOKEN)...")
    guard_active = False
    guard_message = ""
    try:
        rpc_call("htlcgeneratesecret")
    except Exception as e:
        guard_active = True
        guard_message = str(e)
    assert guard_active, "TRU-SWAP RPC guard should reject unauthenticated calls!"
    print(f"    [PASS] Unauthenticated swap RPC call successfully blocked:")
    print(f"           {guard_message}")

    # 3. Execution of Official TRU Swap Regression Suites
    print("\n[*] 3. Running Official Swap Reorg Regression Tests...")
    
    # 3A: swap/reorg_swap_01c_selftest.py
    swap_script_path = "/home/user/git_test/TRU/swap/reorg_swap_01c_selftest.py"
    print(f"    [*] Executing: {os.path.basename(swap_script_path)}...")
    p1 = subprocess.run([sys.executable, swap_script_path],
                        cwd="/home/user/git_test/TRU/swap",
                        capture_output=True, text=True)
    assert p1.returncode == 0, f"Swap 01c failed: {p1.stderr}"
    p1_pass_lines = [l.strip() for l in p1.stdout.splitlines() if "PASS" in l or "OK" in l]
    print(f"    [PASS] reorg_swap_01c completed with returncode 0:")
    for l in p1_pass_lines[:4]:
        print(f"           - {l}")

    # 3B: swap/reorg_exit_01c_selftest.py
    exit_script_path = "/home/user/git_test/TRU/swap/reorg_exit_01c_selftest.py"
    print(f"\n    [*] Executing: {os.path.basename(exit_script_path)}...")
    p2 = subprocess.run([sys.executable, exit_script_path],
                        cwd="/home/user/git_test/TRU/swap",
                        capture_output=True, text=True)
    assert p2.returncode == 0, f"Exit 01c failed: {p2.stderr}"
    p2_pass_lines = [l.strip() for l in p2.stdout.splitlines() if "PASS" in l]
    print(f"    [PASS] reorg_exit_01c completed with returncode 0:")
    for l in p2_pass_lines[:4]:
        print(f"           - {l}")

    result_data = {
        "test_name": "05_swap_htlc",
        "status": "PASS",
        "htlc_sample": {
            "secret_hash160": secret_hash160,
            "refund_lock_time": refund_lock_time,
            "script_hex": htlc_hex,
            "script_size_bytes": len(htlc_hex) // 2
        },
        "rpc_security_guard": {
            "guard_enforced": guard_active,
            "rejection_message": guard_message
        },
        "regression_suites": {
            "reorg_swap_01c": {
                "exit_code": p1.returncode,
                "verifications": p1_pass_lines
            },
            "reorg_exit_01c": {
                "exit_code": p2.returncode,
                "verifications": p2_pass_lines
            }
        }
    }

    out_file = "latest_run_05_swap_htlc_result.json"
    with open(out_file, "w") as f:
        json.dump(result_data, f, indent=2)
    print(f"\n[+] Test artifact saved to: {out_file}\n")
    return result_data

if __name__ == "__main__":
    run_test()
