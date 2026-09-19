# TRU Community Test Suite (TRU-community-tests)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Network](https://img.shields.io/badge/Network-TRU%20Mainnet%2FTestnet-blue.svg)](https://tokenizedrealutility.com)
[![Version](https://img.shields.io/badge/Core%20Target-v0.05%2B-green.svg)](https://github.com/TokenizedRealUtility)
[![Round 1](https://img.shields.io/badge/Round%201-6%2F6%20Passed%20%E2%9C%85-success.svg)](round_1/results/ROUND_1_REPORT.md)
[![Round 2](https://img.shields.io/badge/Round%202-7%2F7%20Passed%20%E2%9C%85-success.svg)](round_2/results/ROUND_2_REPORT.md)

Open-source, independent community test suite and on-chain protocol regression validator for **Tokenized Real Utility (TRU)**.

---

## 🧭 Project Architecture

To ensure long-term scalability and clean separation of concerns, `TRU-community-tests` is structured modularly. Each testing campaign (Round) is organized as an isolated, self-contained suite with its own specification, test modules, and verification artifacts:

```
TRU-community-tests/
├── README.md                      # Master test suite documentation
├── requirements.txt               # Unified Python dependencies
├── .env.example                   # Environment configuration template
├── .gitignore                     # Strict credential & log hygiene
├── run_all.sh                     # Unified shell runner
├── run_all.py                     # Master test execution orchestrator
│
├── round_1/                       # Round 1: Core Protocol Feature Baseline (6/6 Passed)
│   ├── 01_truscriptions_test.py   # TRUScriptions (Ordinals analog)
│   ├── 02_smart_contracts_test.py # CLTV TimeLocks & Voting Gas Models
│   ├── 03_token_evolution_test.py # Neural Living SFT Evolution (Epoch 1 -> 2)
│   ├── 04_web_wallet_backup_test.py# Web Wallet AES Keystore & Signed DID
│   ├── 05_swap_htlc_test.py       # Cross-Chain Atomic Swaps & 15 Reorg Regressions
│   ├── 06_pwa_mobile_miner_test.py# Mobile PWA & WebAssembly Mining Candidate
│   ├── config.py / common.py      # Round 1 helpers
│   ├── run_round1.sh              # Round 1 standalone runner
│   └── results/                   # Verified JSON logs & ROUND_1_REPORT.md
│
└── round_2/                       # Round 2: Core 0.05, VM Limits, Fuzzing (7/7 Passed)
    ├── ROUND_2_TEST_PLAN.md       # Master specification & test definitions
    ├── 01_p2p_recovery_test.py    # [PEER-REDIAL-01] Verified-peer reconnect fuzzing
    ├── 02_logging_rotation_test.py# Core 0.05 bounded logging & 32 MiB rotation
    ├── 03_contract_gas_limits_test.py # VM limits (100k gas, 201 ops, SigOps, MTP)
    ├── 04_token_evolution_attacks_test.py # SFT split-brain & non-owner attack defenses
    ├── 05_mempool_boundaries_test.py # Exact atom/byte fee limits & zero-fee eviction
    ├── 06_did_malleability_test.py# Low-S (BIP62) enforcement & strict DER parsing
    ├── 07_htlc_reorg_edge_test.py # HTLC preimage length fuzzing & race protection
    ├── teardown_and_refund.py     # Automated sweep refund back to treasury
    ├── config.py / common.py      # Round 2 helpers with exact atom/byte sizing
    ├── run_round2.sh              # Round 2 standalone runner
    └── results/                   # Verified JSON logs & ROUND_2_REPORT.md
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- `cryptography` package
- Access to a running TRU Core node (local or remote RPC at port `21832`)

```bash
# Clone the repository
git clone git@github.com:PoWGrid/TRU-community-tests.git
cd TRU-community-tests

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure environment
cp .env.example .env
```

---

## 🚀 Running the Tests

### Execute All Rounds
```bash
# Using the unified shell runner:
./run_all.sh

# Or using Python:
python3 run_all.py
```

### Run a Specific Round
```bash
# Execute only Round 1 (Baseline Features):
./run_all.sh --round 1

# Execute only Round 2 (Core 0.05, VM Limits, Cryptographic Malleability):
./run_all.sh --round 2
```

---

## 🛡️ Protocol Security & Safety Rules

As emphasized by the TRU Core Lead Developer (#348):
> *"One good habit for any test suite: use a fresh test wallet with a small balance, never your main keys."*

1. **Zero Key Exposure:** Tests never require production mining, stealth, or treasury keys.
2. **Ephemeral Burner Wallets:** Public execution defaults to memory-generated ephemeral burner keys on the fly.
3. **Automated Refund Teardown:** In Round 2, `teardown_and_refund.py` sweeps all unspent funds back to the treasury wallet automatically upon test completion.
4. **Exact Atom/Byte Fee Accounting:** Transactions calculate network fees with exact byte precision based on `MIN_RELAY_FEE_ATOM_PER_BYTE = 1` atom/byte.

---

## 📊 Summary of Test Results

### Round 1: Protocol Feature Baseline (6/6 Passed ✅)
See the full [Round 1 Verification Report](round_1/results/ROUND_1_REPORT.md).
- Inscription #1 broadcast & indexed on-chain (`Tx: 280fb35c...`)
- 24-hour CLTV TimeLock deployed (`Tx: aa4710ab...`) & gas models confirmed
- Living Token SFT KRAKEN Epoch 1 -> 2 evolution anchor verified (`Tx: 8cfd8a01...`)
- Web Wallet deterministic derivation, AES-256-GCM keystore & DID verified
- 15/15 HTLC reorg resilience regression tests confirmed
- Mobile PWA / WebAssembly block template mining candidate benchmarked

### Round 2: Core 0.05 Resilience & Edge-Case Fuzzing (7/7 Passed ✅)
See the full [Round 2 Verification Report](round_2/results/ROUND_2_REPORT.md).
- `[PEER-REDIAL-01]` auto-recovery verified with unverified socket table poisoning defense
- Bounded structured logging verified: 32 MiB hard rotation limit, 4-tier `.1`..`.4` archive retention
- VM limits enforced: 210-opcode griefing transaction rejected fail-closed; CLTV Median-Time-Past guard verified
- Living SFT split-brain attack (forged `prevHash`) and non-owner mutation rejected fail-closed
- Mempool sub-minimum fee (< 1 atom/byte) and zero-fee transactions evicted
- Cryptographic malleability: canonical Low-S (BIP62) accepted; High-S and non-canonical DER rejected
- HTLC preimage length fuzzing confirmed strict 32-byte enforcement

---

## 🤝 Contributing Future Rounds

New testing campaigns (e.g. `round_3/`) can be added seamlessly:
1. Create directory `round_N/` following the established layout.
2. Implement feature or fuzzing modules (`01_*_test.py`, `02_*_test.py`, etc.).
3. Register the round in `run_all.py`.
4. Ensure all tests utilize ephemeral test wallets and adhere to security rules.

---

## 📜 License
MIT License. See [LICENSE](LICENSE) for details.
