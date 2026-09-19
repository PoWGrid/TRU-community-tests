#!/usr/bin/env python3
"""
TRU Round 2 Teardown & Balance Refund
Sweeps all unspent TRU from Round 2 Test Wallet back to Funder Vault / Treasury
using exact atom/byte fee calculation.
"""

import os
import sys
import json
import time
from common import (
    rpc_call,
    get_spendable_utxo,
    estimate_tx_vsize,
    calculate_exact_relay_fee,
    atoms_to_tru,
    tru_to_atoms,
    print_banner
)
import config

def refund():
    print_banner("TEARDOWN & FULL BALANCE REFUND TO FUNDER VAULT")

    test_addr = config.TEST_ADDRESS
    test_priv = config.TEST_PRIVKEY_HEX
    vault_addr = config.VAULT_ADDRESS

    if not vault_addr:
        print("[!] No TRU_VAULT_ADDRESS configured in environment or .env. Skipping refund.")
        return

    print(f"[*] Source Test Wallet: {test_addr}")
    print(f"[*] Destination Vault:  {vault_addr}")

    # Fetch all spendable UTXOs for test wallet
    utxos = rpc_call("listunspent", {"address": test_addr})
    if not utxos:
        print("[!] No spendable UTXOs found on test wallet. Balance already clean.")
        return

    total_atoms = sum(tru_to_atoms(float(u["amount"])) for u in utxos if u.get("spendable", False))
    print(f"[*] Total Test Wallet Balance: {atoms_to_tru(total_atoms)} TRU ({total_atoms} atoms)")

    inputs = [{"txid": u["txid"], "vout": u["vout"]} for u in utxos if u.get("spendable", False)]
    vin_count = len(inputs)

    # 1 sweep output back to KRAKEN Vault
    vout_count = 1
    vsize = estimate_tx_vsize(vin_count, vout_count)
    
    # Exact fee calculation (1 atom/byte, minimum standard 10,000 atoms = 0.0001 TRU)
    fee_atoms = max(10000, calculate_exact_relay_fee(vsize, atom_per_byte=1))
    fee_tru = atoms_to_tru(fee_atoms)

    refund_atoms = total_atoms - fee_atoms
    refund_tru = atoms_to_tru(refund_atoms)

    print(f"[*] Transaction Inputs:  {vin_count} UTXO(s)")
    print(f"[*] Estimated VSize:     {vsize} bytes")
    print(f"[*] Exact Network Fee:   {fee_tru:.8f} TRU ({fee_atoms} atoms)")
    print(f"[*] Total Refund Amount: {refund_tru:.8f} TRU ({refund_atoms} atoms) -> {vault_addr}")

    raw_tx_params = {
        "inputs": inputs,
        "outputs": {
            vault_addr: refund_tru
        }
    }
    raw_hex = rpc_call("createrawtransaction", raw_tx_params)
    sign_res = rpc_call("signrawtransactionwithkey", {"txHex": raw_hex, "privKeys": [test_priv]})
    if not sign_res.get("complete"):
        raise RuntimeError(f"Refund transaction signing failed: {sign_res}")

    signed_hex = sign_res["hex"]
    actual_bytes = len(signed_hex) // 2
    print(f"[+] Signed Sweep Transaction: {actual_bytes} bytes")
    print(f"[+] Effective Fee Rate: {fee_atoms / actual_bytes:.2f} atoms/byte")

    broadcast_res = rpc_call("sendrawtransaction", {"txHex": signed_hex})
    txid = broadcast_res.get("txid") if isinstance(broadcast_res, dict) else broadcast_res
    print(f"🎉 Refund Broadcast Successfully! TXID: {txid}")

    time.sleep(1)
    vault_bal = rpc_call("getbalance", {"address": vault_addr})
    test_bal = rpc_call("getbalance", {"address": test_addr})
    print(f"\n[+] Funder Vault Balance Restored: {vault_bal.get('confirmed', vault_bal)} TRU")
    print(f"[+] Round 2 Test Wallet Balance Cleaned: {test_bal.get('confirmed', test_bal)} TRU")

if __name__ == "__main__":
    refund()
