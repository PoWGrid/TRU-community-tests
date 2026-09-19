#!/usr/bin/env python3
"""
Configuration Loader for TRU Round 2 Community Tests
Loads configuration from:
1. Environment variables
2. .env file (if present)
3. Ephemeral burner key generation (if no key is provided)
"""

import os
import sys
import json
import hashlib
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

def load_dotenv():
    env_paths = [
        os.path.join(BASE_DIR, ".env"),
        os.path.join(ROOT_DIR, ".env")
    ]
    for env_file in env_paths:
        if os.path.exists(env_file):
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass

load_dotenv()

DEFAULT_RPC_URL = "http://127.0.0.1:21832/rpc"
DEFAULT_KRAKEN_TOKEN_ID = "4af48028c201dbff"
DEFAULT_KRAKEN_ORIGIN_ADDR = "TQWoB1FwWSFp5hDcFV5FzNvQG6kne2sxJr"
DEFAULT_VAULT_ADDRESS = ""

RPC_URL = os.getenv("TRU_RPC_URL", DEFAULT_RPC_URL)
TOKEN_ID = os.getenv("TRU_TOKEN_ID", DEFAULT_KRAKEN_TOKEN_ID)
RPC_COOKIE_PATH = os.getenv("TRU_RPC_COOKIE_PATH", "")
RPC_AUTH_TOKEN = os.getenv("TRU_RPC_AUTH_TOKEN", "")

# Ephemeral Burner Key or Injected Test Wallet
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    res = []
    while n > 0:
        n, r = divmod(n, 58)
        res.append(B58_ALPHABET[r])
    pad = 0
    for byte in b:
        if byte == 0: pad += 1
        else: break
    return "1" * pad + "".join(reversed(res))

def base58_check_encode(prefix: bytes, payload: bytes) -> str:
    data = prefix + payload
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    return b58encode(data + checksum)

def derive_secp256k1(priv_hex: str):
    from cryptography.hazmat.primitives.asymmetric import ec
    priv_int = int(priv_hex, 16)
    priv_key = ec.derive_private_key(priv_int, ec.SECP256K1())
    pub_key = priv_key.public_key()
    x_bytes = pub_key.public_numbers().x.to_bytes(32, "big")
    prefix = b"\x02" if pub_key.public_numbers().y % 2 == 0 else b"\x03"
    comp_pub = prefix + x_bytes
    sha = hashlib.sha256(comp_pub).digest()
    h160 = hashlib.new("ripemd160", sha).digest()
    addr = base58_check_encode(b"\x41", h160)
    return addr, comp_pub.hex()

# 1. Try environment variable
env_key = os.getenv("TRU_TEST_PRIVKEY", "").strip()

# 2. Try local non-versioned test wallet file
wallet_file = os.path.join(BASE_DIR, "test_wallets", "round2_test_wallet.json")
local_key = ""
local_addr = ""
local_pub = ""

if os.path.exists(wallet_file):
    try:
        with open(wallet_file, "r") as f:
            wdata = json.load(f)
            local_key = wdata.get("priv_hex", "")
            local_addr = wdata.get("address", "")
            local_pub = wdata.get("pub_hex", "")
    except Exception:
        pass

if env_key:
    TEST_PRIVKEY_HEX = env_key
    TEST_ADDRESS, TEST_PUBKEY_HEX = derive_secp256k1(TEST_PRIVKEY_HEX)
elif local_key:
    TEST_PRIVKEY_HEX = local_key
    TEST_ADDRESS = local_addr
    TEST_PUBKEY_HEX = local_pub
else:
    # 3. Dynamic Ephemeral Burner Key (Pure Memory, Zero On-Disk Storage)
    rnd_priv = secrets.randbits(256)
    TEST_PRIVKEY_HEX = f"{rnd_priv:064x}"
    TEST_ADDRESS, TEST_PUBKEY_HEX = derive_secp256k1(TEST_PRIVKEY_HEX)

# Destination Treasury / Vault for sweep refunds
VAULT_ADDRESS = os.getenv("TRU_VAULT_ADDRESS", DEFAULT_VAULT_ADDRESS)
