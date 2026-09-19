# TRU Core Protocol Community Test Suite (Round 1)

[![TRU Community Test Suite](https://img.shields.io/badge/Testnet-Round--1-blue.svg)](https://github.com/powgrid/tru-community-tests)
[![Results](https://img.shields.io/badge/Results-6%2F6%20Passed-brightgreen.svg)](round_1_results/ROUND_1_REPORT.md)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)

An independent, reproducible test suite and on-chain verification framework for the **Tokenized Real Utility (TRU)** protocol. 

This repository allows **anyone to test TRU core features using their own private keys, node RPC, and wallets**, while also serving as an immutable record of the official **Round 1 Community Testnet Audit**.

---

## 🎯 Features Covered

| # | Test Suite | Protocol Layer | On-Chain Verification |
|---|------------|----------------|-----------------------|
| **01** | **TRUSCRIPTIONS** (`01_truscriptions_test.py`) | On-Chain Ordinals / Inscriptions | Broadcasts canonical OP_RETURN inscription envelope (`type: TRUSCRIPT`) |
| **02** | **Smart Contracts** (`02_smart_contracts_test.py`) | Contract VM / CLTV / Gas Model | Deploys 24h TimeLock contract; verifies consensus time-barrier & voting contract gas limits |
| **03** | **Living Token Evolution** (`03_token_evolution_test.py`) | Neural SFT Living Tokens | Evolves SFT token metadata via `TRU_EVOLVE_V1` state transition anchor |
| **04** | **Web Wallet & Backups** (`04_web_wallet_backup_test.py`) | Browser Self-Custody / Identity | Proves secp256k1 derivation, AES-256-GCM keystore backup & `registerDIDSigned` zero-disclosure proof |
| **05** | **Cross-Chain HTLC Swaps** (`05_swap_htlc_test.py`) | Atomic Swaps & Bridges | Cryptographic preimage hashlock / timelock scripts & 15-case reorg resilience regression suite |
| **06** | **Mobile PWA & Browser Mining** (`06_pwa_mobile_miner_test.py`) | WebAssembly PoW Engine | Fetches restricted `TRU-WEB-MINER-01` candidate template and benchmarks double-SHA256 loop |

---

## 🚀 Quick Start: Run Tests with Your Own Keys

### 1. Clone the Repository
```bash
git clone https://github.com/powgrid/tru-community-tests.git
cd tru-community-tests
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your Environment (`.env`)
Copy the template configuration:
```bash
cp .env.example .env
```

Edit `.env` with your preferred settings:
```ini
# TRU Node RPC Configuration
TRU_RPC_URL=http://127.0.0.1:21832/rpc
# Optional: path to RPC auth cookie if required by node
TRU_COOKIE_PATH=

# Your Wallet Credentials
# If provided, your address will be derived automatically via secp256k1
TRU_PRIVATE_KEY=your_private_key_hex_here

# Target Token ID for evolution test (e.g. your SFT or the demo KRAKEN token)
TRU_TOKEN_ID=4af48028c201dbff
```

> **Note:** If `.env` is omitted, the test suite falls back to the default KRAKEN community demo credentials and local RPC at `http://127.0.0.1:21832/rpc`.

### 4. Run All Tests
```bash
./run_all.sh
# or
python3 run_all_tests.py
```

### 5. Run Individual Feature Tests
```bash
python3 01_truscriptions_test.py
python3 02_smart_contracts_test.py
python3 03_token_evolution_test.py
python3 04_web_wallet_backup_test.py
python3 05_swap_htlc_test.py
python3 06_pwa_mobile_miner_test.py
```

---

## 📜 Round 1 On-Chain Verification Artifacts

The initial Round 1 audit was executed against TRU Mainnet/Testnet block `#8472`. All results and on-chain proofs are documented in:
- 📑 **[Complete Round 1 Technical Report](round_1_results/ROUND_1_REPORT.md)**
- 📁 **[Raw JSON Execution Artifacts](round_1_results/)**

### Round 1 Summary Matrix

```
====================================================================================================
TRU PROTOCOL COMMUNITY AUDIT & TEST SUITE - ROUND 1
====================================================================================================
TEST SCRIPT                      PROTOCOL LAYER            STATUS     TIME (s)   TXID / PROOF
----------------------------------------------------------------------------------------------------
01_truscriptions_test.py         TRUSCRIPT Inscriptions    PASS       1.10s      280fb35ce8eda823...
02_smart_contracts_test.py       TimeLock CLTV & Gas VM    PASS       0.10s      aa4710abf8dc9f12...
03_token_evolution_test.py       Living SFT Evolution      PASS       1.07s      8cfd8a01ad184dc0...
04_web_wallet_backup_test.py     Client Keystore & DID     PASS       0.10s      did:on_tru:e700d...
05_swap_htlc_test.py             Cross-Chain HTLC Swaps    PASS       1.42s      15 Reorg Cases OK
06_pwa_mobile_miner_test.py      PWA / Web-Miner PoW       PASS       0.08s      2.11 MH/s @ WebW...
====================================================================================================
OVERALL: 6/6 PASSED (100.0%) - Total Time: 4.18s
====================================================================================================
```

### Verified On-Chain Transactions

- **TRUSCRIPT Inscription #1:**
  - `TxID: 280fb35ce8eda82313fbf9f72a17b3536ee7d123e3639d32bd81af49810bca3e`
  - Inscription payload size: 326 bytes
- **Smart Contract (24h CLTV TimeLock):**
  - `TxID: aa4710abf8dc9f12379a0f002a741ed6c25a04344be1ba128d5e520e5cc11773`
  - Contract Output: `aa4710abf8dc9f12379a0f002a741ed6c25a04344be1ba128d5e520e5cc11773:1`
- **Living SFT Evolution (Epoch 1 -> Epoch 2):**
  - `TxID: 8cfd8a01ad184dc042ae7c3771546de2c3e19e0a5357162d0955cefee50ca413`
  - Anchor: `TRU_EVOLVE_V1` for token `4af48028c201dbff`
- **Decentralized Identity (Zero-Disclosure Ownership):**
  - DID: `did:on_tru:e700d587dc5dd2dc`

---

## 🔒 Security & Best Practices

- **Zero Private Key Transmission:** Private keys are never passed as parameters to node RPC calls. Inscription transactions, evolution anchors, and DID ownership challenges are signed locally using strict canonical Low-S ECDSA signatures (`common.py`).
- **UTXO Preservation:** The test suite verifies standard 25-byte P2PKH script types and excludes mempool-spent outputs to avoid accidental consumption of contract outputs or token control UTXOs.
- **Credential Protection:** `.env` is ignored by `.gitignore`. Do not commit private keys to version control.

---

## 📄 License
MIT License. Maintained by the **PoWGrid Community** ([powgrid.xyz](https://powgrid.xyz)).
