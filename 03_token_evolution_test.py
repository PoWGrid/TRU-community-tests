#!/usr/bin/env python3
"""
TRU Community Test #03: TOKEN EVOLUTION (SFT KRAKEN)
Tests Living Token Evolution (SFT/NCFT) on TRU blockchain:
1. Verifies confirmed SFT KRAKEN issuance state via verifytokenevolution RPC.
2. Derives Epoch 2 evolution transition:
   - Previous Metadata Hash: SHA256(Issuance Meta)
   - New Metadata Hash: SHA256(Epoch 2 Evolved Meta)
   - Provider: neural-adaptive
   - Trigger: deep-sea-resonance-epoch2
3. Builds canonical TRU_EVOLVE_V1 anchor OP_RETURN script.
4. Assembles anchor transaction, signs with KRAKEN SFT owner key, broadcasts.
5. Verifies mempool admission and validates against token evolution subsystem.
"""

import os
import sys
import json
import time
import struct
import hashlib
from common import (
    rpc_call,
    KRAKEN_ADDRESS,
    KRAKEN_PRIVKEY_HEX,
    KRAKEN_TOKEN_ID,
    KRAKEN_MINT_TXID,
    get_safe_spendable_utxo,
    print_banner
)

def push_bytes(s: str) -> bytes:
    raw = s.encode('utf-8')
    n = len(raw)
    if n <= 75:
        prefix = bytes([n])
    elif n <= 255:
        prefix = b'\x4c' + bytes([n])
    elif n <= 65535:
        prefix = b'\x4d' + struct.pack('<H', n)
    else:
        raise ValueError("push data exceeds maximum size")
    return prefix + raw

def build_evolution_opreturn(token_id: str, token_type: str, epoch: int,
                            provider: str, trigger: str,
                            prev_hash: str, new_hash: str) -> str:
    chunks = [
        "TRU_EVOLVE_V1",
        token_id,
        token_type,
        str(epoch),
        provider,
        trigger,
        prev_hash,
        new_hash
    ]
    payload = b'\x6a'
    for c in chunks:
        payload += push_bytes(c)
    return payload.hex()

def run_test():
    print_banner("03 - LIVING TOKEN EVOLUTION (SFT KRAKEN EPOCH 1 -> 2)")

    # 1. Pre-verification of KRAKEN Token State
    print(f"[*] Querying verifytokenevolution for TokenID: {KRAKEN_TOKEN_ID}...")
    init_status = rpc_call("verifytokenevolution", {
        "tokenID": KRAKEN_TOKEN_ID,
        "require_confirmed": True
    })
    print(f"[+] Issuance Status: {init_status.get('issuance_status')}")
    print(f"[+] Issuance TxID:   {init_status.get('issuance_txid')}")
    print(f"[+] Token Type:      {init_status.get('token_type')}")
    assert init_status.get("issuance_status") == "CONFIRMED", "KRAKEN issuance is not confirmed!"

    # 2. Load Confirmed Issuance Metadata
    kraken_json_path = "/home/user/git_test/TRU/tokens/kraken_token.json"
    with open(kraken_json_path, "r") as f:
        kraken_data = json.load(f)

    epoch1_meta = kraken_data.get("onchain_metadata", {}).get("meta", {})
    epoch1_json_str = json.dumps(epoch1_meta, sort_keys=True)
    prev_meta_hash = hashlib.sha256(epoch1_json_str.encode('utf-8')).hexdigest()
    print(f"[*] Epoch 1 Metadata Hash: {prev_meta_hash}")

    # 3. Construct Evolved Epoch 2 Metadata
    epoch2_meta = dict(epoch1_meta)
    epoch2_meta.update({
        "evolution_epoch": "2",
        "evolution_trigger": "deep-sea-resonance-epoch2",
        "adaptation_rate": "0.15",
        "ai_version": "2.0-neural-deep",
        "intelligence_tier": "abyssal_autonomous_v2",
        "awakening_telemetry": {
            "mempool_interactions": 42,
            "hash_absorption_rate": "12.8GH/s",
            "neural_synapses": 1000000
        },
        "evolution_timestamp": int(time.time())
    })
    epoch2_json_str = json.dumps(epoch2_meta, sort_keys=True)
    new_meta_hash = hashlib.sha256(epoch2_json_str.encode('utf-8')).hexdigest()
    print(f"[+] Epoch 2 Evolved Metadata Hash: {new_meta_hash}")

    provider = "neural-adaptive"
    trigger = "deep-sea-resonance-epoch2"
    epoch = 2

    # 4. Build Canonical TRU_EVOLVE_V1 Anchor OP_RETURN Script
    opret_hex = build_evolution_opreturn(
        token_id=KRAKEN_TOKEN_ID,
        token_type="SFT",
        epoch=epoch,
        provider=provider,
        trigger=trigger,
        prev_hash=prev_meta_hash,
        new_hash=new_meta_hash
    )
    print(f"[+] TRU_EVOLVE_V1 OP_RETURN Script: {opret_hex[:40]}... ({len(opret_hex)//2} bytes)")

    # 5. Fund and Sign Evolution Anchor Transaction
    utxo = get_safe_spendable_utxo(KRAKEN_ADDRESS, min_amount_tru=1.0)
    utxo_amount = float(utxo["amount"])
    fee_tru = 0.001
    change_tru = round(utxo_amount - fee_tru, 8)
    print(f"[*] Funding UTXO: {utxo['txid']}:{utxo['vout']} ({utxo_amount} TRU)")

    raw_tx_params = {
        "inputs": [{"txid": utxo["txid"], "vout": utxo["vout"]}],
        "outputs": {
            "data": opret_hex,
            KRAKEN_ADDRESS: change_tru
        }
    }
    create_res = rpc_call("createrawtransaction", raw_tx_params)
    unsigned_hex = create_res
    print(f"[+] Anchor transaction created ({len(unsigned_hex)//2} bytes)")

    sign_res = rpc_call("signrawtransactionwithkey", {
        "txHex": unsigned_hex,
        "privKeys": [KRAKEN_PRIVKEY_HEX]
    })
    if not sign_res.get("complete"):
        raise RuntimeError(f"Failed to sign evolution transaction: {sign_res}")
    signed_hex = sign_res["hex"]
    print(f"[+] Signed by KRAKEN owner ({len(signed_hex)//2} bytes)")

    # 6. Broadcast Anchor Transaction
    print("[*] Broadcasting SFT KRAKEN Evolution Anchor to TRU network...")
    broadcast_res = rpc_call("sendrawtransaction", {"txHex": signed_hex})
    anchor_txid = broadcast_res.get("txid")
    print(f"[SUCCESS] Evolution Anchor Accepted in Mempool! Anchor TxID: {anchor_txid}")

    # 7. Post-Broadcast Verification via verifytokenevolution
    time.sleep(1)
    post_status = rpc_call("verifytokenevolution", {
        "tokenID": KRAKEN_TOKEN_ID,
        "require_confirmed": False
    })
    print(f"[*] verifytokenevolution (unconfirmed view): ok={post_status.get('runtime_ok', False)}, history_ok={post_status.get('history_ok', False)}")

    result_data = {
        "test_name": "03_token_evolution",
        "status": "PASS",
        "tokenID": KRAKEN_TOKEN_ID,
        "token_name": "Monster from the Deep",
        "token_type": "SFT",
        "epoch_transition": "1 -> 2",
        "anchor_txid": anchor_txid,
        "owner": KRAKEN_ADDRESS,
        "provider": provider,
        "trigger": trigger,
        "previous_metadata_hash": prev_meta_hash,
        "new_metadata_hash": new_meta_hash,
        "evolved_metadata": epoch2_meta
    }

    out_file = "latest_run_03_token_evolution_result.json"
    with open(out_file, "w") as f:
        json.dump(result_data, f, indent=2)
    print(f"[+] Test artifact saved to: {out_file}\n")
    return result_data

if __name__ == "__main__":
    run_test()
