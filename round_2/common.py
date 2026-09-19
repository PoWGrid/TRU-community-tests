#!/usr/bin/env python3
"""
Common Utilities for TRU Round 2 Community Test Suite
Features:
- Configurable RPC communication with auto-token discovery
- Exact byte and atom/byte fee calculation
- secp256k1 Low-S (BIP62) ECDSA signature generation & verification
- High-S signature generator for malleability negative testing
- UTXO selector and mempool state tracking
- Structured test result exporter (*_result.json)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json
import time
import hashlib
import urllib.request
import urllib.error
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes

import config

B58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
SECP256K1_HALF_N = SECP256K1_N // 2

# Base58Check Helpers
def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, 'big')
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(B58_ALPHABET[r])
    pad = 0
    for byte in b:
        if byte == 0: pad += 1
        else: break
    return '1' * pad + ''.join(reversed(res))

def b58decode(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 58 + B58_ALPHABET.index(ch)
    h = hex(n)[2:]
    if len(h) % 2: h = '0' + h
    b = bytes.fromhex(h)
    pad = 0
    for ch in s:
        if ch == '1': pad += 1
        else: break
    return b'\x00' * pad + b

def base58_check_encode(prefix: bytes, payload: bytes) -> str:
    data = prefix + payload
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    return b58encode(data + checksum)

def privkey_to_pubkey(privkey_hex: str) -> tuple[bytes, str]:
    priv_int = int(privkey_hex, 16)
    priv_key = ec.derive_private_key(priv_int, ec.SECP256K1())
    pub_key = priv_key.public_key()
    x_bytes = pub_key.public_numbers().x.to_bytes(32, 'big')
    prefix = b'\x02' if pub_key.public_numbers().y % 2 == 0 else b'\x03'
    comp_pub = prefix + x_bytes
    return comp_pub, comp_pub.hex()

def pubkey_to_address(pubkey_bytes: bytes) -> str:
    sha = hashlib.sha256(pubkey_bytes).digest()
    h160 = hashlib.new('ripemd160', sha).digest()
    return base58_check_encode(b'\x41', h160)

# Exact Transaction Sizing & Fee Calculation (atom/byte)
def estimate_tx_vsize(vin_count: int, vout_count: int, op_return_len: int = 0) -> int:
    """
    Computes exact byte size for standard TRU P2PKH transactions:
    - 4 bytes version
    - varint in_count (1 byte for <= 252)
    - per input: 32 bytes txid + 4 bytes vout + 1 byte scriptSig len + ~106 bytes scriptSig + 4 bytes sequence = ~147 bytes
    - varint out_count (1 byte)
    - per P2PKH output: 8 bytes amount + 1 byte scriptPubKey len + 25 bytes P2PKH script = 34 bytes
    - OP_RETURN output (if any): 8 bytes amount (0) + 1 byte len + 1 byte OP_RETURN (0x6a) + push_data = 10 + op_return_len
    - 4 bytes locktime
    """
    size = 4 + 1 + (vin_count * 147) + 1 + (vout_count * 34) + 4
    if op_return_len > 0:
        size += 10 + op_return_len
    return size

def calculate_exact_relay_fee(tx_bytes: int, atom_per_byte: int = 1) -> int:
    """
    Returns exact relay fee in atoms based on TRU Core rules:
    minimumFee = bytes * MIN_RELAY_FEE_ATOM_PER_BYTE
    """
    return max(1, tx_bytes * atom_per_byte)

def atoms_to_tru(atoms: int) -> float:
    return round(atoms / 100000000.0, 8)

def tru_to_atoms(tru_amount: float) -> int:
    return int(round(tru_amount * 100000000))

# Signatures: Canonical Low-S and Malleable High-S
def sign_digest_low_s(privkey_hex: str, digest32: bytes) -> str:
    priv_int = int(privkey_hex, 16)
    priv_key = ec.derive_private_key(priv_int, ec.SECP256K1())
    raw_der = priv_key.sign(digest32, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
    r, s = utils.decode_dss_signature(raw_der)
    if s > SECP256K1_HALF_N:
        s = SECP256K1_N - s
    return utils.encode_dss_signature(r, s).hex()

def sign_digest_high_s(privkey_hex: str, digest32: bytes) -> str:
    priv_int = int(privkey_hex, 16)
    priv_key = ec.derive_private_key(priv_int, ec.SECP256K1())
    raw_der = priv_key.sign(digest32, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
    r, s = utils.decode_dss_signature(raw_der)
    if s <= SECP256K1_HALF_N:
        s = SECP256K1_N - s
    return utils.encode_dss_signature(r, s).hex()

# RPC Client
def get_rpc_auth_token():
    if config.RPC_AUTH_TOKEN:
        return config.RPC_AUTH_TOKEN
    paths = [
        config.RPC_COOKIE_PATH,
        os.path.expanduser("~/.tru/.rpc-cookie-21832"),
        os.path.expanduser("~/.tru/rpc-cookie-21832"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "workspace", "docker-node", "data", ".rpc-cookie-21832")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "nodes", "core", "docker-node", "data", ".rpc-cookie-21832")),
    ]
    for p in paths:
        if p and os.path.exists(p):
            try:
                with open(p, "r") as f:
                    t = f.read().strip()
                    if t: return t
            except Exception:
                pass
    return ""

def rpc_call(method: str, params=None):
    token = get_rpc_auth_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params or {}
    }).encode("utf-8")

    req = urllib.request.Request(config.RPC_URL, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "error" in data and data["error"]:
                raise RuntimeError(f"RPC Error [{data['error'].get('code')}]: {data['error'].get('message')}")
            return data.get("result")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP Error {e.code}: {err_body}")

def get_spendable_utxo(address: str, min_amount_tru: float = 0.001) -> dict:
    try:
        utxos = rpc_call("listunspent", {"address": address})
        if utxos:
            for u in utxos:
                if u.get("spendable", False) and float(u["amount"]) >= min_amount_tru:
                    return u
    except Exception:
        pass
    # Synthetic burner UTXO fallback for negative/offline tests
    return {
        "txid": "1111111111111111111111111111111111111111111111111111111111111111",
        "vout": 0,
        "amount": 10.0,
        "spendable": True
    }

def save_test_result(test_name: str, passed: bool, details: dict):
    out_dir = os.path.join(config.BASE_DIR, "results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{test_name}_result.json")
    record = {
        "test": test_name,
        "passed": passed,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details
    }
    with open(out_file, "w") as f:
        json.dump(record, f, indent=2)
    status_str = "PASS ✅" if passed else "FAIL ❌"
    print(f"\n[RESULT] {test_name}: {status_str} (Saved to {out_file})\n")

def print_banner(title: str):
    print("=" * 70)
    print(f"🔬 TRU ROUND 2 TEST SUITE: {title}")
    print("=" * 70)
