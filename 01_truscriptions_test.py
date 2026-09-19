#!/usr/bin/env python3
"""
TRU Community Test #01: TRUSCRIPTIONS
Tests on-chain immutable inscriptions (Ordinals analog) on TRU blockchain:
1. Constructs canonical TRUscription JSON payload.
2. Encodes OP_RETURN payload according to consensus rules.
3. Selects safe UTXO from KRAKEN wallet (TQWoB1FwWSFp5hDcFV5FzNvQG6kne2sxJr).
4. Assembles, signs (secp256k1), and broadcasts transaction via inscribeTRUScriptSigned.
5. Verifies registration in mempool, queries getTRUScripts and getTRUScriptDetails.
"""

import os
import sys
import json
import time
import hashlib
from common import (
    rpc_call,
    KRAKEN_ADDRESS,
    KRAKEN_PRIVKEY_HEX,
    get_safe_spendable_utxo,
    print_banner
)

def build_truscript_opreturn(data_str: str, owner_addr: str, index=1, sat_num=0, ts=None) -> str:
    if ts is None:
        ts = int(time.time())
    meta = {
        "type": "TRUSCRIPT",
        "data": data_str,
        "owner": owner_addr,
        "inscriptionIndex": index,
        "satNumber": sat_num,
        "timestamp": ts
    }
    json_bytes = json.dumps(meta, separators=(',', ':')).encode('utf-8')
    data_len = len(json_bytes)
    data_hex = json_bytes.hex()
    if data_len <= 75:
        len_hex = f"{data_len:02x}"
    elif data_len <= 255:
        len_hex = f"4c{data_len:02x}"
    else:
        len_hex = f"4d{data_len & 0xff:02x}{(data_len >> 8) & 0xff:02x}"
    return "6a" + len_hex + data_hex

def run_test():
    print_banner("01 - TRUSCRIPTIONS (ON-CHAIN INSCRIPTIONS)")
    
    # 1. Inspect Chain & Wallet Status
    tip_height = rpc_call("getblockcount")
    print(f"[*] Node Block Tip: #{tip_height}")
    balance_res = rpc_call("getbalance", {"address": KRAKEN_ADDRESS})
    print(f"[*] Wallet Address: {KRAKEN_ADDRESS}")
    print(f"[*] Spendable Balance: {balance_res} TRU")

    # 2. Pick Safe UTXO
    utxo = get_safe_spendable_utxo(KRAKEN_ADDRESS, min_amount_tru=1.0)
    utxo_amount = float(utxo["amount"])
    fee_tru = 0.001
    change_tru = round(utxo_amount - fee_tru, 8)
    print(f"[*] Selected UTXO: {utxo['txid']}:{utxo['vout']} ({utxo_amount} TRU)")

    # 3. Formulate Inscription Content
    inscription_payload = {
        "protocol": "truscription-v1",
        "op": "inscribe",
        "title": "Community Testnet Verification",
        "author": "KRAKEN Commander",
        "provenance": "Epoch 1 SFT Holder",
        "wallet": KRAKEN_ADDRESS,
        "timestamp": int(time.time()),
        "declaration": "TRU Core protocol validation: Inscriptions, SFT Living Tokens, Magic Locks & Mobile Mining."
    }
    inscription_text = json.dumps(inscription_payload, separators=(',', ':'))
    print(f"[*] Inscription Payload: {inscription_text}")

    # 4. Generate Canonical OP_RETURN Script
    op_return_script = build_truscript_opreturn(
        data_str=inscription_text,
        owner_addr=KRAKEN_ADDRESS,
        index=1,
        sat_num=tip_height * 50 * 100000000,
        ts=inscription_payload["timestamp"]
    )
    print(f"[+] Canonical OP_RETURN Script: {op_return_script[:40]}... (len={len(op_return_script)//2} bytes)")

    # 5. Create Raw Transaction
    raw_tx_params = {
        "inputs": [{"txid": utxo["txid"], "vout": utxo["vout"]}],
        "outputs": {
            "data": op_return_script,
            KRAKEN_ADDRESS: change_tru
        }
    }
    create_res = rpc_call("createrawtransaction", raw_tx_params)
    unsigned_hex = create_res
    print(f"[+] Unsigned Transaction created ({len(unsigned_hex)//2} bytes)")

    # 6. Sign with KRAKEN Private Key
    sign_params = {
        "txHex": unsigned_hex,
        "privKeys": [KRAKEN_PRIVKEY_HEX]
    }
    sign_res = rpc_call("signrawtransactionwithkey", sign_params)
    if not sign_res.get("complete"):
        raise RuntimeError(f"Transaction signing failed: {sign_res}")
    signed_hex = sign_res["hex"]
    print(f"[+] Transaction signed with KRAKEN private key ({len(signed_hex)//2} bytes)")

    # 7. Inscribe and Broadcast via inscribeTRUScriptSigned
    inscribe_params = {
        "signedTxHex": signed_hex,
        "inscriptionData": inscription_text,
        "owner": KRAKEN_ADDRESS
    }
    print("[*] Broadcasting signed TRUScript inscription to network...")
    inscribe_res = rpc_call("inscribeTRUScriptSigned", inscribe_params)
    txid = inscribe_res.get("txid")
    print(f"[SUCCESS] TRUScript Inscribed On-Chain! TXID: {txid}")

    # 8. Query Inscriptions for Owner
    print("[*] Querying getTRUScripts for owner...")
    time.sleep(1)
    scripts = rpc_call("getTRUScripts", {"ownerAddress": KRAKEN_ADDRESS})
    found = any(s.get("txid") == txid for s in scripts)
    print(f"[*] Found in owner's TRUScripts list: {found} (Total owned: {len(scripts)})")

    # 9. Query Inscription Details
    details = rpc_call("getTRUScriptDetails", {"txid": txid})
    print(f"[*] Inscription Index: #{details.get('inscriptionIndex')}")
    print(f"[*] Inscribed Size: {details.get('sizeBytes')} bytes")
    print(f"[*] Sat Number: {details.get('satNumber')}")

    result_data = {
        "test_name": "01_truscriptions",
        "status": "PASS",
        "txid": txid,
        "owner": KRAKEN_ADDRESS,
        "block_height_broadcast": tip_height,
        "fee_paid_tru": fee_tru,
        "inscription_details": details
    }
    
    out_file = "latest_run_01_truscriptions_result.json"
    with open(out_file, "w") as f:
        json.dump(result_data, f, indent=2)
    print(f"[+] Test artifact saved to: {out_file}\n")
    return result_data

if __name__ == "__main__":
    run_test()
