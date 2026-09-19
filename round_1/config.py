#!/usr/bin/env python3
"""
Configuration Loader for TRU Community Tests
Loads configuration from:
1. Command-line arguments (--key, --rpc, --token)
2. Environment variables or .env file
3. Fallback defaults (Round-1 KRAKEN verification keys)
"""

import os
import sys
import argparse

# Default Round-1 Verification Settings
DEFAULT_RPC_URL = "http://127.0.0.1:21832/rpc"
DEFAULT_KRAKEN_ADDRESS = "TQWoB1FwWSFp5hDcFV5FzNvQG6kne2sxJr"
DEFAULT_KRAKEN_TOKEN_ID = "4af48028c201dbff"
DEFAULT_KRAKEN_MINT_TXID = "7e4c3fc6c9b4caf18c1bb34773439ceec83246d22e1536ac035e4cf367d5273b"

def load_dotenv():
    env_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    ]
    for env_file in env_paths:
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v

load_dotenv()

RPC_URL = os.getenv("TRU_RPC_URL", DEFAULT_RPC_URL)
RPC_COOKIE_PATH = os.getenv("TRU_RPC_COOKIE_PATH", "")
RPC_AUTH_TOKEN = os.getenv("TRU_RPC_AUTH_TOKEN", "")

PRIVATE_KEY = os.getenv("TRU_PRIVATE_KEY", "").strip()
TOKEN_ID = os.getenv("TRU_TOKEN_ID", DEFAULT_KRAKEN_TOKEN_ID).strip()
