#!/usr/bin/env python3
"""
Common Utilities for TRU Community Test Suite
- Configurable RPC Communication (Cookies, Auth Token, Custom URLs)
- Dynamic secp256k1 Address & Key Derivation from User Config
- Safe UTXO Selection (Consensus P2PKH verification + Mempool spend exclusion)
- Formatting and Serialization
"""

import os
import sys
import json
import time
import struct
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

# Cryptographic Key & Address Derivation
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

def sign_digest_der(privkey_hex: str, digest32: bytes) -> str:
    priv_int = int(privkey_hex, 16)
    priv_key = ec.derive_private_key(priv_int, ec.SECP256K1())
    raw_der = priv_key.sign(digest32, ec.ECDSA(utils.Prehashed(hashes.SHA256())))
    r, s = utils.decode_dss_signature(raw_der)
    if s > SECP256K1_HALF_N:
        s = SECP256K1_N - s
    return utils.encode_dss_signature(r, s).hex()

# Active User Key & Address Derived Automatically from .env / CLI / Defaults
USER_PRIVKEY_HEX = config.PRIVATE_KEY
USER_PUBKEY_BYTES, USER_PUBKEY_HEX = privkey_to_pubkey(USER_PRIVKEY_HEX)
USER_ADDRESS = pubkey_to_address(USER_PUBKEY_BYTES)
TARGET_TOKEN_ID = config.TOKEN_ID

# Aliases for scripts
KRAKEN_ADDRESS = USER_ADDRESS
KRAKEN_PRIVKEY_HEX = USER_PRIVKEY_HEX
KRAKEN_TOKEN_ID = TARGET_TOKEN_ID
KRAKEN_MINT_TXID = config.DEFAULT_KRAKEN_MINT_TXID

def get_rpc_auth_token():
    if config.RPC_AUTH_TOKEN:
        return config.RPC_AUTH_TOKEN
    
    paths = []
    if config.RPC_COOKIE_PATH:
        paths.append(config.RPC_COOKIE_PATH)
    paths.extend([
        os.path.expanduser("~/.tru/rpc-cookie-21832"),
        "/home/user/git_test/TRU/docker-node/data/.rpc-cookie-21832",
        "../TRU/docker-node/data/.rpc-cookie-21832",
        "./data/.rpc-cookie-21832"
    ])
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    t = f.read().strip()
                    if t: return t
            except Exception:
                pass
    return ""

def rpc_call(method, params=None):
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

def get_mempool_spent_outpoints():
    spent = set()
    try:
        raw_txs = rpc_call("getmempooltransactions")
        for hex_str in raw_txs:
            if len(hex_str) >= 80:
                txid_hex = hex_str[10:74]
                vout_bytes = bytes.fromhex(hex_str[74:82])
                vout = struct.unpack('<I', vout_bytes)[0]
                spent.add(f"{txid_hex}:{vout}")
    except Exception:
        pass
    return spent

def get_safe_spendable_utxo(address: str, min_amount_tru=0.01):
    utxos = rpc_call("listunspent", {"address": address})
    if not utxos:
        raise RuntimeError(f"No spendable UTXOs found for address: {address}")

    mempool_spent = get_mempool_spent_outpoints()
    candidates = []
    for u in utxos:
        outpoint = f"{u['txid']}:{u['vout']}"
        if outpoint in mempool_spent:
            continue
        script = u.get("scriptPubKey", "")
        # Standard P2PKH script only (exclude contracts / token controls)
        if len(script) == 50 and script.startswith("76a914") and script.endswith("88ac"):
            if float(u["amount"]) >= min_amount_tru:
                candidates.append(u)

    if not candidates:
        raise RuntimeError(f"No safe standard P2PKH UTXO with balance >= {min_amount_tru} TRU available for {address}")

    candidates.sort(key=lambda x: x.get("confirmations", 0), reverse=True)
    return candidates[0]

def print_banner(title: str):
    print("\n" + "=" * 78)
    print(f"  TRU COMMUNITY TEST SUITE: {title}")
    print("=" * 78)
