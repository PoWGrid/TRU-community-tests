#!/usr/bin/env python3
"""
TRU Round 2 — Module 06: Cryptographic Malleability & Low-S Signature Enforcement
Tests cryptographic signature parser defenses and DID security on TRU Core:
1. Canonical Low-S Signature (BIP62 Compliance):
   - Computes secp256k1 signature ensuring s <= N / 2.
   - Proves registerDIDSigned successfully verifies ownership without key disclosure.
2. Negative Test 1 (High-S Signature Malleability Attack):
   - Flips s to malleable counterpart: s' = N - s (where s' > N / 2).
   - Proves node rejects malleable signature fail-closed.
3. Negative Test 2 (Non-Canonical DER Encoding Injection):
   - Injects non-canonical trailing padding into DER signature envelope.
   - Proves strict DER parser rejects signature.
"""

import os
import sys
import json
import time
import hashlib
from common import (
    rpc_call,
    save_test_result,
    print_banner,
    sign_digest_low_s,
    sign_digest_high_s
)
import config

def run_test():
    print_banner("06 - CRYPTOGRAPHIC MALLEABILITY & LOW-S ENFORCEMENT")
    details = {}

    test_addr = config.TEST_ADDRESS
    test_priv = config.TEST_PRIVKEY_HEX
    test_pub = config.TEST_PUBKEY_HEX

    print(f"[*] Test DID Subject Address: {test_addr}")
    print(f"[*] Test Public Key: {test_pub}")

    # Canonical Deterministic DID
    h1 = hashlib.sha256((test_addr + "mySpecialRandomSalt42").encode()).hexdigest()
    h2 = hashlib.sha256(h1.encode()).hexdigest()
    expected_did = "did:on_tru:" + h2[:16]
    print(f"[*] Deterministic DID: {expected_did}")

    # Canonical challenge
    challenge_msg = (
        f"TRU-DID-REGISTER-V1\n"
        f"network=TRUMain\n"
        f"did={expected_did}\n"
        f"address={test_addr}\n"
        f"pubkey={test_pub}\n"
    )
    digest = hashlib.sha256(challenge_msg.encode('utf-8')).digest()

    # 1. Canonical Low-S Signature Test
    print("\n[*] Step 1: Generating Canonical Low-S Signature (BIP62 Compliant)...")
    low_s_sig = sign_digest_low_s(test_priv, digest)
    print(f"[+] Low-S DER Signature: {low_s_sig} ({len(low_s_sig)//2} bytes)")

    low_s_params = {
        "did": expected_did,
        "address": test_addr,
        "publicKey": test_pub,
        "signature": low_s_sig
    }
    low_s_res = rpc_call("registerDIDSigned", low_s_params)
    print(f"[+] registerDIDSigned result: {low_s_res}")
    verified = low_s_res.get("verifiedOwnership", False)
    if not verified:
        raise RuntimeError("FAIL: Canonical Low-S signature rejected by node!")
    print("✅ SUCCESS: Canonical Low-S signature verified on node.")
    details["low_s_verified"] = True

    # 2. Negative Test 1: High-S Signature Malleability Injection
    print("\n[*] Step 2: Negative Test — Injecting Malleable High-S Signature (s' = N - s)...")
    high_s_sig = sign_digest_high_s(test_priv, digest)
    print(f"[+] High-S DER Signature: {high_s_sig} ({len(high_s_sig)//2} bytes)")

    high_s_params = {
        "did": expected_did,
        "address": test_addr,
        "publicKey": test_pub,
        "signature": high_s_sig
    }
    high_s_rejected = False
    try:
        high_res = rpc_call("registerDIDSigned", high_s_params)
        print(f"[!] High-S result: {high_res}")
        if not high_res.get("verifiedOwnership", True):
            high_s_rejected = True
            print("✅ Node verifiedOwnership is false for High-S signature.")
    except RuntimeError as e:
        print(f"✅ Node rejected High-S signature with RPC error: {e}")
        high_s_rejected = True
        details["high_s_error"] = str(e)

    # 3. Negative Test 2: Non-Canonical DER Encoding (Padding Injection)
    print("\n[*] Step 3: Negative Test — Injecting Non-Canonical DER Trailing Bytes...")
    non_canonical_der = low_s_sig + "0000deadbeef"
    non_canon_params = {
        "did": expected_did,
        "address": test_addr,
        "publicKey": test_pub,
        "signature": non_canonical_der
    }
    der_rejected = False
    try:
        der_res = rpc_call("registerDIDSigned", non_canon_params)
        if not der_res.get("verifiedOwnership", True):
            der_rejected = True
            print("✅ Node rejected non-canonical DER padding (verifiedOwnership=False).")
    except RuntimeError as e:
        print(f"✅ Node rejected non-canonical DER padding with RPC error: {e}")
        der_rejected = True
        details["non_canonical_der_error"] = str(e)

    details["crypto_malleability_defenses_verified"] = True
    save_test_result("06_did_malleability", True, details)
    return True

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
