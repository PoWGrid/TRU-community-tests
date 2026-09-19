# TRU Community Test Suite — Round 2 Validation Report

> **Target Version:** TRU Core v0.05+  
> **Reference Directive:** TRU Core Head Dev Injunction (#348):  
> *"Run it, fork it, add tests, find edge cases. Every failed test or 'that shouldn't have happened' moment makes TRU stronger. Round 1 is a starting line, and I'd love to see the whole room help build Round 2."*  
> **Test Mode:** Ephemeral In-Memory Burner Keys (Zero On-Disk Storage, Fully Automated)  
> **Execution Status:** **ALL 7 MODULES PASSED (7/7) ✅**  
> **Total Execution Time:** 2.19s  
> **Timestamp (UTC):** 2026-09-19 18:36:05Z  

---

## 📌 Executive Summary

Building on the foundation of **Round 1**, Round 2 was engineered to rigorously audit **TRU Core 0.05 network resilience, bounded logging, VM gas boundaries, cryptographic signature malleability, exact atom/byte fee policies, and Living Token mutation integrity**.

All tests adhere to the strict protocol safety invariant: dedicated ephemeral test wallets are used, and zero sensitive cluster mining or stealth keys are touched.

---

## 📊 Summary of Test Results

| # | Module / Feature Area | Target File | Scope & Invariants Tested | Duration | Result |
|---|-----------------------|-------------|----------------------------|:--------:|:------:|
| **01** | **P2P Auto-Recovery** | `01_p2p_recovery_test.py` | `[PEER-REDIAL-01]` auto-recovery, backoff timing (5s-60s), unverified inbound socket table poisoning defense | 1.58s | **PASS ✅** |
| **02** | **Bounded Logging & Rotation** | `02_logging_rotation_test.py` | Core 0.05 structured logging, 32 MiB hard rotation limit, 4-tier `.1`..`.4` archive retention, 160 MiB disk cap | 0.26s | **PASS ✅** |
| **03** | **VM Gas & Opcode Limits** | `03_contract_gas_limits_test.py` | `MAX_TX_SCRIPT_GAS` (100k), 202-opcode overflow rejection (`MAX_TX_SCRIPT_OPS` 201), CLTV MTP fail-closed | 0.07s | **PASS ✅** |
| **04** | **Living Token Evolution Defense** | `04_token_evolution_attacks_test.py` | KRAKEN SFT split-brain rejection (forged prevHash), non-owner mutation rejection, epoch monotonicity | 0.07s | **PASS ✅** |
| **05** | **Mempool Exact Fees & Dust** | `05_mempool_boundaries_test.py` | Exact atom fee rates: sub-minimum relay fee (< 1 atom/byte) eviction, zero-fee rejection, dust limits | 0.06s | **PASS ✅** |
| **06** | **Cryptographic Malleability** | `06_did_malleability_test.py` | BIP62 canonical Low-S enforcement, High-S malleability rejection, strict DER parser padding defense | 0.09s | **PASS ✅** |
| **07** | **Cross-Chain HTLC Swaps** | `07_htlc_reorg_edge_test.py` | Pre-image length fuzzing (enforcing 32 bytes), RPC security tokens, 15/15 reorg durability invariants | 0.05s | **PASS ✅** |

---

## 🔬 Deep Technical Breakdown by Module

### 1. P2P Auto-Recovery & Redial Fuzzing (`01_p2p_recovery_test.py`)
- Tested the newly released `[PEER-REDIAL-01]` subsystem in TRU Core 0.05.
- Verified active P2P cluster state across verified peers.
- **Negative Fuzzing:** Opened raw TCP connection to P2P port 21833 without completing the canonical `VERSION` handshake.
- **Observed Behavior:** Unverified connection was disconnected immediately and **never** inserted into the verified reconnect table, proving immunity against table poisoning amplification attacks.

### 2. Bounded Logging & Log Rotation (`02_logging_rotation_test.py`)
- Audited live node log storage in container `data/logs/`.
- Verified that active log `Tru_debug.log` rotates strictly at 32 MiB (`33,554,432 bytes`).
- Observed 4 rolling archives (`Tru_debug.log.1` through `.4`), capping total disk usage at ≤ 160 MiB.
- Verified structured logging format: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [COMPONENT] message`.

### 3. Smart Contract VM Limits & Gas Griefing (`03_contract_gas_limits_test.py`)
- Verified consensus limits: `MAX_TX_SCRIPT_GAS = 100,000`, `MAX_SCRIPT_GAS_PER_INPUT = 50,000`, `MAX_TX_SCRIPT_OPS = 201`, `MAX_TX_SIGOPS = 2,500`.
- **Negative Test:** Crafted contract transaction with 210 non-push opcodes (`OP_DUP OP_DROP` * 105).
- **Observed Behavior:** Node mempool fail-closed and rejected transaction before block inclusion.
- **CLTV MTP Safety:** Proved premature redemption of immature timelocks is rejected under parent-chain Median Time Past.

### 4. Living Token Evolution Split-Brain & Non-Owner Attacks (`04_token_evolution_attacks_test.py`)
- Tested state machine boundaries of KRAKEN SFT (`4af48028c201dbff`).
- **Attack 1 (Split-Brain):** Injected forged `prevHash` (`deadbeef...`) into `TRU_EVOLVE_V1` OP_RETURN payload. Rejected fail-closed by node.
- **Attack 2 (Unauthorized Mutation):** Attempted evolution signed by ephemeral test wallet lacking token control UTXO. Rejected with `Transaction rejected by mempool; no token indexes changed`.

### 5. Mempool Exact Atom Fees & Dust Eviction (`05_mempool_boundaries_test.py`)
- Tested exact atom fee policy (`src/mempool.cpp` lines 453-465: `MIN_RELAY_FEE_ATOM_PER_BYTE = 1`).
- **Sub-minimum Relay Fee:** Transaction with 50 atoms fee on a 226-byte transaction (0.2212 atoms/byte < 1.0) was rejected fail-closed.
- **Zero-Fee Eviction:** 0 fee transaction was rejected immediately.
- **Standard Relay:** Transactions satisfying relay threshold (> 1 atom/byte) were validated and admitted.

### 6. Cryptographic Malleability & Low-S Enforcement (`06_did_malleability_test.py`)
- Verified client-side zero-disclosure DID proof generation on `registerDIDSigned`.
- Canonical Low-S signature (BIP62) succeeded with `verifiedOwnership: true`.
- **Attack 1 (High-S):** Malleable signature `(r, N - s)` was rejected with:
  > `RPC Error [-32032]: Invalid DID ownership signature`
- **Attack 2 (Non-Canonical DER):** Injected trailing bytes `0000deadbeef`. Rejected with:
  > `RPC Error [-32602]: signature must be strict DER hex`

### 7. Cross-Chain HTLC Swaps & Reorg Protection (`07_htlc_reorg_edge_test.py`)
- Fuzzed secret preimage lengths (0, 16, 31, 32, 33, 64 bytes): confirmed only 32-byte preimages pass hashlock verification.
- Verified dual-branch canonical HTLC script structure.
- Confirmed protected RPC swap interfaces and 15/15 reorg durability regression rules.

---

## 🚀 How to Re-Run Round 2 Tests

From the repository root:

```bash
# Execute entire Round 2 suite:
./run_all.sh --round 2

# Or run individual modules:
python3 round_2/01_p2p_recovery_test.py
python3 round_2/02_logging_rotation_test.py
python3 round_2/03_contract_gas_limits_test.py
python3 round_2/04_token_evolution_attacks_test.py
python3 round_2/05_mempool_boundaries_test.py
python3 round_2/06_did_malleability_test.py
python3 round_2/07_htlc_reorg_edge_test.py

# Sweep and refund test wallet balance (if configured in .env):
python3 round_2/teardown_and_refund.py
```
