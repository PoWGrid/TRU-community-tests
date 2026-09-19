# TRU Protocol Community Test Suite — Round 2 Specification & Test Plan

> **Workspace:** `round_2/`  
> **Target Version:** TRU Core v0.05+  
> **Reference Directive:** TRU Core Head Dev Injunction (#348):  
> *"Run it, fork it, add tests, find edge cases. Every failed test or 'that shouldn't have happened' moment makes TRU stronger. Round 1 is a starting line, and I'd love to see the whole room help build Round 2. One good habit for any test suite: use a fresh test wallet with a small balance, never your main keys."*

---

## 📋 Executive Overview

Following the successful execution and official acceptance of **Round 1** (6/6 features validated on-chain in `round_1/`), **Round 2** shifts focus from baseline functional validation to **deep protocol edge cases, stress testing, negative regression vectors, and Core 0.05 architectural additions**.

### Key Protocol Areas Covered in Round 2:
1. **Core 0.05 P2P Auto-Recovery Fuzzing (`[PEER-REDIAL-01]`)**
2. **Core 0.05 Bounded Logging & Log Rotation Under Load**
3. **Smart Contract VM Bounds, Gas Griefing & Opcode Limits**
4. **Living Token Evolution (SFT) Integrity & Split-Brain Resistance**
5. **Mempool Boundary Conditions, Dust, and Double-Spend Conflict Eviction**
6. **DID Cryptographic Malleability & Low-S Signature Enforcement**
7. **Cross-Chain HTLC State Machine & Reorg Edge Cases**

---

## 🔒 Test Environment & Safety Rules (Mandatory)

1. **Isolated Test Wallet:**
   - In accordance with Head Dev's warning, **never** use the main cluster mining or stealth key wallets.
   - Tests generate ephemeral in-memory burner wallets by default, or accept an optional test wallet via `.env`.
2. **Non-Destructive Execution:**
   - Tests running against live network nodes must not destabilize active mining loops.
   - Node-level stress tests (P2P reconnect and log rotation) must run against designated test RPC endpoints or isolated local instances.
3. **Machine-Readable Standard:**
   - Every module outputs structured JSON test results (`*_result.json`) including exit code, timing, logs, and assertions.

---

## 🧪 Comprehensive List of Round 2 Test Suites

```
round_2/
├── ROUND_2_TEST_PLAN.md               <-- Master Specification
├── config.py                          <-- Environment & Node RPC Configuration
├── common.py                          <-- Reusable RPC, crypto & assertion helpers
├── run_round2.sh                      <-- Automated runner for Round 2
├── run_round2.py                      <-- Python test orchestrator
├── 01_p2p_recovery_test.py            <-- Suite 01: Peer Redial & Network Recovery
├── 02_logging_rotation_test.py        <-- Suite 02: Bounded Log Rotation & I/O Stress
├── 03_contract_gas_limits_test.py     <-- Suite 03: VM Limits, Gas & CLTV Boundaries
├── 04_token_evolution_attacks_test.py <-- Suite 04: SFT Evolution Negative Vectors
├── 05_mempool_boundaries_test.py      <-- Suite 05: Mempool Dust & Conflict Eviction
├── 06_did_malleability_test.py        <-- Suite 06: Low-S, DER & Signature Malleability
└── 07_htlc_reorg_edge_test.py         <-- Suite 07: Atomic Swap Expiry Race Conditions
```

---

## 🔬 Detailed Module Specifications

### Module 01: Core 0.05 P2P Auto-Recovery Fuzzing (`01_p2p_recovery_test.py`)
*Objective:* Rigorously stress test the new `[PEER-REDIAL-01]` automatic verified-peer reconnect subsystem introduced in Core 0.05.

- **Test 1.1 — Verified Peer Reconnect & Exponential Backoff:**
  - *Setup:* Connect a mock verified peer; complete the `VERSION` handshake.
  - *Action:* Abruptly sever TCP connection.
  - *Assertion:* Core detects disconnect, schedules redial with base delay (~5s), doubles with deterministic jitter up to 60s max.
- **Test 1.2 — Unverified Inbound Poisoning Prevention (Negative Test):**
  - *Setup:* Open raw TCP connection without sending valid `VERSION` handshake, then close.
  - *Assertion:* Node must *never* add unverified IP:port to the reconnect table (`peers.size()` unchanged).
- **Test 1.3 — Ban & Abuse Score Eviction Interaction:**
  - *Action:* Induce protocol abuse score threshold (>100) on a peer.
  - *Assertion:* Banned peer is purged from reconnect candidates and never redialed while `now < bannedUntil`.
- **Test 1.4 — Reconnect Thread Shutdown Budget:**
  - *Action:* Trigger node shutdown while reconnect thread is waiting on backoff timer.
  - *Assertion:* Reconnect loop exits cleanly within the 2.0s shutdown budget without hang.

---

### Module 02: Bounded Logging & Log Rotation Under Load (`02_logging_rotation_test.py`)
*Objective:* Verify that Core 0.05 completely eliminates unbounded log growth (`Tru_debug.log`) under high-throughput RPC and block broadcast.

- **Test 2.1 — Log Level Suppression:**
  - *Action:* Configure node with `minimumLevel = "INFO"`. Emit `DEBUG` and `TRACE` events via RPC.
  - *Assertion:* Suppressed events do not write to disk; log size remains static.
- **Test 2.2 — Hard 32 MiB Rotation Threshold:**
  - *Action:* Stream controlled log volume until threshold.
  - *Assertion:* File wraps at exactly 32 MiB (`33,554,432 bytes`), moving `Tru_node.log` to `Tru_node.log.1`.
- **Test 2.3 — 4-Tier Rolling Retention Cap:**
  - *Action:* Trigger 6 consecutive rotation cycles.
  - *Assertion:* Exactly 4 archived logs (`.1`, `.2`, `.3`, `.4`) exist; oldest (`.5`) is unlinked; total directory size ≤ 160 MiB.
- **Test 2.4 — Multi-Threaded Logging Lock Contention:**
  - *Action:* High-frequency logging from multiple parallel worker threads.
  - *Assertion:* Zero mutex deadlocks; zero message interleaving or truncated lines.

---

### Module 03: Smart Contract VM Limits & Gas Griefing (`03_contract_gas_limits_test.py`)
*Objective:* Confirm deterministic consensus rejection when smart contract script execution exceeds VM security boundaries.

- **Test 3.1 — Max Gas Exhaustion (`MAX_TX_SCRIPT_GAS = 100,000`):**
  - *Action:* Deploy/execute contract script whose cumulative opcode gas cost exceeds 100,000 units.
  - *Assertion:* Node returns `-32000 Script Gas Limit Exceeded`; transaction rejected from mempool.
- **Test 3.2 — Per-Input Gas Limit (`MAX_SCRIPT_GAS_PER_INPUT = 50,000`):**
  - *Action:* Construct multi-input transaction where one input script consumes 55,000 gas.
  - *Assertion:* Evaluates fail-closed; transaction discarded.
- **Test 3.3 — Opcode Limit Griefing (`MAX_TX_SCRIPT_OPS = 201`):**
  - *Action:* Submit script containing 202 non-push opcodes (e.g. repeated `OP_DUP OP_DROP`).
  - *Assertion:* Rejection with `Script Opcode Limit Exceeded`.
- **Test 3.4 — Max SigOps Boundary (`MAX_TX_SIGOPS = 2,500`):**
  - *Action:* Submit transaction packing > 2,500 `OP_CHECKSIG` operations.
  - *Assertion:* Rejected before VM execution to protect block validation latency.
- **Test 3.5 — CLTV Locktime Against Median-Time-Past (MTP):**
  - *Action:* Attempt redemption at `current_height` when `MTP < lockTime`.
  - *Assertion:* Rejected under consensus rule `Time Lock has not matured under parent-chain MTP`.

---

### Module 04: Living Token Evolution Integrity & Negative Vectors (`04_token_evolution_attacks_test.py`)
*Objective:* Probe SFT / Living Token state transition integrity (KRAKEN token family) against state tampering and split-brain mutations.

- **Test 4.1 — Stale / Mismatched Previous Hash Rejection:**
  - *Action:* Submit `TRU_EVOLVE_V1` OP_RETURN payload where `prevHash` does not match the on-chain Epoch 2 anchor (`b16208a8...`).
  - *Assertion:* Node indexes reject evolution as invalid provenance state; token state stays at Epoch 2.
- **Test 4.2 — Unauthorized Evolution Signature (Non-Owner Mutation):**
  - *Action:* Sign evolution transaction using a key that does not own the SFT token UTXO.
  - *Assertion:* Rejected by node consensus validation (`Unauthorized Token Evolution Attempt`).
- **Test 4.3 — Epoch Replay / Epoch Skip Prevention:**
  - *Action:* Attempt evolution directly from Epoch 2 to Epoch 4 (skipping Epoch 3), or replay Epoch 2 payload.
  - *Assertion:* Strict monotonic sequence check enforces sequential increments.
- **Test 4.4 — Malformed Metadata Inscription Payload:**
  - *Action:* Inject corrupted UTF-8 / non-conforming JSON payload into evolution envelope.
  - *Assertion:* Gracefully rejected without indexing corruption.

---

### Module 05: Mempool Boundaries, Dust, and Conflict Eviction (`05_mempool_boundaries_test.py`)
*Objective:* Verify mempool resistance to denial-of-service, zero-fee flooding, and double-spend griefing.

- **Test 5.1 — Zero-Fee Transaction Eviction:**
  - *Action:* Broadcast raw transaction with 0 fee.
  - *Assertion:* Node responds with `-32000 Min Relay Fee Not Met`.
- **Test 5.2 — Dust Limit Enforcement:**
  - *Action:* Create transaction output with value below consensus dust threshold (< 0.00001 TRU).
  - *Assertion:* Transaction rejected as dust.
- **Test 5.3 — Double-Spend Conflict Eviction:**
  - *Action:* Broadcast TX_A spending Outpoint X, then broadcast TX_B spending Outpoint X with higher fee.
  - *Assertion:* Validate node's mempool replacement policy (RBF or first-seen policy).
- **Test 5.4 — Unconfirmed Ancestor Chain Depth:**
  - *Action:* Broadcast a sequence of unconfirmed chained transactions exceeding maximum allowed ancestor count.
  - *Assertion:* Exceeding transactions rejected cleanly.

---

### Module 06: Cryptographic Malleability & DID Security (`06_did_malleability_test.py`)
*Objective:* Audit secp256k1 signature validation and DID registrations against cryptographic malleability vectors.

- **Test 6.1 — High-S Signature Rejection (BIP62 Compliance):**
  - *Action:* Generate valid signature `(r, s)`. Compute high-S equivalent `(r, N - s)`. Submit to `registerDIDSigned`.
  - *Assertion:* Node rejects high-S signature to prevent transaction malleability.
- **Test 6.2 — Non-Canonical DER Encoding Injection:**
  - *Action:* Inject padding bytes, extra length headers, or non-minimal integers into DER signature payload.
  - *Assertion:* Strict parser rejects signature; ownership verification fails.
- **Test 6.3 — Challenge Replay & Expiry Resistance:**
  - *Action:* Re-submit a previously verified `TRU-DID-REGISTER-V1` signature with stale timestamp / used challenge.
  - *Assertion:* Replay detected and rejected.
- **Test 6.4 — Keystore Tamper Proofing:**
  - *Action:* Flip single bits in AES-256-GCM ciphertext, auth tag, and IV.
  - *Assertion:* GCM authentication tag verification fails immediately; zero key leakage.

---

### Module 07: Cross-Chain Atomic Swaps (HTLC) Reorg & State Machine (`07_htlc_reorg_edge_test.py`)
*Objective:* Verify atomic swap state machine under boundary conditions and race conditions.

- **Test 7.1 — Simultaneous Claim & Refund Race Condition:**
  - *Action:* Mine block exactly at `lockTime` boundary; submit both pre-image claim and CLTV refund.
  - *Assertion:* Consensus deterministically resolves priority without stuck funds.
- **Test 7.2 — Preimage Length Fuzzing:**
  - *Action:* Attempt claim with preimages of length 0, 16, 31, 33, and 64 bytes.
  - *Assertion:* Only exact 32-byte preimages matching hashlock are accepted.
- **Test 7.3 — RPC Token Security Boundary:**
  - *Action:* Query swap management RPCs with missing, expired, or spoofed `TRU_SWAP_RPC_TOKEN`.
  - *Assertion:* Strict `-32000` rejection.

---

## 📊 Implementation Roadmap & Execution Plan

| Step | Milestone | Deliverable | Status |
|:----:|:----------|:------------|:------:|
| **1** | Directory & Spec Setup | `round_2/ROUND_2_TEST_PLAN.md` | **COMPLETED ✅** |
| **2** | Core Test Infrastructure | `config.py`, `common.py`, dedicated test wallet | **COMPLETED ✅** |
| **3** | Core 0.05 Features | `01_p2p_recovery_test.py`, `02_logging_rotation_test.py` | **COMPLETED ✅** |
| **4** | VM & SFT Edge Cases | `03_contract_gas_limits_test.py`, `04_token_evolution_attacks_test.py` | **COMPLETED ✅** |
| **5** | Crypto & Mempool Suite | `05_mempool_boundaries_test.py`, `06_did_malleability_test.py` | **COMPLETED ✅** |
| **6** | Atomic Swaps & Runner | `07_htlc_reorg_edge_test.py`, `run_round2.sh` | **COMPLETED ✅** |
| **7** | Round 2 Report & PR | `ROUND_2_REPORT.md` submitted for community & dev review | **COMPLETED ✅** |

---
*Created for TRU Core Developers & Community Testing Initiative.*
