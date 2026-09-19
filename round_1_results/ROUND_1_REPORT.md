# TRU Community Test Suite & Official Feature Validation Report

> **Network:** Tokenized Real Utility (TRU) Mainnet / Incentivized Testnet  
> **Testing Suite Directory:** `TRU/community_tests/`  
> **Wallet Tested:** `TQWoB1FwWSFp5hDcFV5FzNvQG6kne2sxJr` (KRAKEN SFT Origin & Gas Wallet)  
> **TokenID Tested:** `4af48028c201dbff` ("Monster from the Deep" SFT)  
> **Execution Status:** **ALL 6 FEATURE SUITES PASSED (6/6) ✅**

---

## 📌 Executive Summary

Following requests from the TRU Core Lead Developer, this comprehensive test suite independently audits, executes, and confirms the operation of all key protocol features:

1. **TRUSCRIPTIONS** (On-Chain Inscriptions / Ordinals Analog)
2. **Smart Contracts** (TimeLock CLTV Contracts & Voting Contract Gas Model)
3. **Living Token Evolution** (SFT KRAKEN Evolution from Epoch 1 to Epoch 2)
4. **Web Wallet & Backups** (Browser Self-Custody, Encrypted Keystore & Signed DID)
5. **Cross-Chain HTLC Swaps & Bridges** (HTLC Engine, Reorg Resilience & RPC Guards)
6. **Mobile PWA & Browser Mining** (Canonical Work Candidate & WebAssembly Engine)

All tests are designed to be reproducible, non-destructive, and natively integrated with TRU Core node consensus rules and RPC endpoints.

---

## 📊 Summary of Test Results

| # | Feature / Test Module | Protocol Layer | Execution Time | On-Chain Action | Result |
|---|----------------------|----------------|:--------------:|:---------------:|:------:|
| **01** | **TRUSCRIPTIONS** (`01_truscriptions_test.py`) | Inscription Envelope | ~1.10s | Broadcast Inscription TX | **PASS ✅** |
| **02** | **Smart Contracts** (`02_smart_contracts_test.py`) | Contract VM / CLTV | ~0.10s | Deploy 24h TimeLock TX | **PASS ✅** |
| **03** | **Token Evolution** (`03_token_evolution_test.py`) | Neural Living Tokens | ~1.07s | Broadcast Evolution Anchor | **PASS ✅** |
| **04** | **Web Wallet & Backups** (`04_web_wallet_backup_test.py`) | Browser Self-Custody | ~0.10s | Verify Signed DID Proof | **PASS ✅** |
| **05** | **Cross-Chain HTLC Swaps** (`05_swap_htlc_test.py`) | Atomic Swap Reorg | ~1.42s | 15 Reorg Regressions | **PASS ✅** |
| **06** | **Mobile PWA Mining** (`06_pwa_mobile_miner_test.py`) | WEB-MINER-01 Engine | ~0.08s | Candidate PoW Benchmark | **PASS ✅** |

---

## 🔬 Detailed Technical Breakdown by Feature

### 1. TRUSCRIPTIONS (`01_truscriptions_test.py`)
- **Objective:** Verify inscription of arbitrary immutable data directly on the TRU blockchain.
- **Implementation:**
  - Standard OP_RETURN push format (`0x6a` + length push + canonical JSON).
  - Pushes: `type: "TRUSCRIPT"`, `data`, `owner`, `inscriptionIndex`, `satNumber`, `timestamp`.
  - Transaction signed with KRAKEN private key and submitted via `inscribeTRUScriptSigned`.
- **Observed Results:**
  - Inscription Transaction: `280fb35ce8eda82313fbf9f72a17b3536ee7d123e3639d32bd81af49810bca3e`
  - Inscription Index: `#1`
  - Inscribed Payload Size: `326 bytes`
  - Sat Number (cumulative genesis atoms): `1,622,461,440`
  - Successfully indexed in `tokenMetadata:<txid>` and discoverable via `getTRUScripts` / `getTRUScriptDetails`.

---

### 2. Smart Contracts: TimeLock & Voting Gas Model (`02_smart_contracts_test.py`)
- **Part A: TimeLock Contract (CLTV):**
  - Canonical bytecode: `04 <LE-u32 lockTime> b1 75 76 a9 14 <hash160> 88 ac` (64 hex characters / 32 bytes).
  - Deployed through `createcontracttransaction` (Type: `TIMELOCK`, Value: 1.0 TRU, Lock duration: 24 hours).
  - Broadcast Transaction: `aa4710abf8dc9f12379a0f002a741ed6c25a04344be1ba128d5e520e5cc11773`
  - Active Contract Address: `aa4710abf8dc9f12379a0f002a741ed6c25a04344be1ba128d5e520e5cc11773:1`
  - **Consensus Safety Test:** Calling `redeemtimelock` before maturity fails closed as required by protocol consensus:
    > `RPC Error [-32000]: Time Lock redemption failed: Time Lock has not matured under parent-chain MTP`
  - **Confirmation:** Confirmed on-chain in Block `#8470`.

- **Part B: Voting Contract & Gas Limits:**
  - Audited on-chain live contract: `9f77feb0276f07e9c1f1e2dafb3c24ee1ca40adc277930b4fc475f7b8717d225:1` (`voting_v1` family).
  - VM Gas Limits verified:
    - `MAX_TX_SCRIPT_GAS`: **100,000** gas units
    - `MAX_SCRIPT_GAS_PER_INPUT`: **50,000** gas units
    - `MAX_TX_SCRIPT_OPS`: **201** ops
    - `MAX_TX_SIGOPS`: **2,500** sigops
  - Envelope standard: `TRUCALL` (version `0x01`, 48-byte payload, commits to `SHA256(scriptSig)` preventing argument tampering).

---

### 3. Living Token Evolution (`03_token_evolution_test.py`)
- **Objective:** Progress the KRAKEN SFT (`4af48028c201dbff`) from Epoch 1 to Epoch 2.
- **Issuance Verification:**
  - Token: "Monster from the Deep" (KRAKEN)
  - Issuance TX: `7e4c3fc6c9b4caf18c1bb34773439ceec83246d22e1536ac035e4cf367d5273b` (Block #4859)
  - Current Status: `CONFIRMED`
- **Evolution Provenance Transition:**
  - **Previous Metadata Hash (Epoch 1):** `2b1c8ea19a52a207834bdb6d4ed6531dda035e4e42a16405dc7824ebb3fc7fc9`
  - **New Metadata Hash (Epoch 2):** `b16208a8f0b41002b2e01667c8f2cfa57331c8df8506c11ead83b5e696dbeead`
  - **Provider:** `neural-adaptive`
  - **Trigger:** `deep-sea-resonance-epoch2`
- **Canonical Payload (`TRU_EVOLVE_V1`):**
  - 8-push OP_RETURN payload: `["TRU_EVOLVE_V1", tokenID, "SFT", "2", provider, trigger, prevHash, newHash]`.
  - Evolution Anchor TxID: `8cfd8a01ad184dc042ae7c3771546de2c3e19e0a5357162d0955cefee50ca413` (Confirmed in Block #8472).

---

### 4. Web Wallet & Backups (`04_web_wallet_backup_test.py`)
- **Objective:** Validate client-side browser self-custody standards without server-side key exposure.
- **Tests & Proofs:**
  1. **Deterministic Address Derivation:** Pure client-side derivation of `TQWoB1FwWSFp5hDcFV5FzNvQG6kne2sxJr` from raw private key via secp256k1 + SHA256 + RIPEMD160 + Base58Check (Version `0x41`).
  2. **Encrypted Keystore Backup:** Export to AES-256-GCM encrypted keystore using PBKDF2-HMAC-SHA256 (100,000 iterations).
  3. **Tamper Rejection:** Proves decryption fails immediately with invalid passphrases or altered ciphertexts.
  4. **Signed DID Proof (`registerDIDSigned`):**
     - Deterministic DID: `did:on_tru:e700d587dc5dd2dc`
     - Signed canonical registration challenge `TRU-DID-REGISTER-V1` locally with secp256k1 canonical Low-S DER signature.
     - Submitted to `registerDIDSigned` RPC.
     - Node verified ownership (`verifiedOwnership: true`) with zero disclosure of private keys.

---

### 5. Cross-Chain HTLC Swaps & Bridges (`05_swap_htlc_test.py`)
- **Objective:** Test atomic swap hash-time locks and reorg resilience.
- **Cryptographic HTLC Construction:**
  - 32-byte secret preimage with RIPEMD160 hashlock and CLTV refund timelock.
  - Canonical dual-branch Bitcoin/TRU script: `OP_IF OP_HASH160 <hash> OP_EQUALVERIFY <claimPubkey> OP_CHECKSIG OP_ELSE <time> OP_CHECKLOCKTIMEVERIFY OP_DROP <refundPubkey> OP_CHECKSIG OP_ENDIF`.
- **Security Guard Audit:**
  - Calling swap RPC without authentication is rejected with:
    > `RPC Error [-32000]: TRU-SWAP RPC disabled: TRU_SWAP_RPC_TOKEN is not configured`
  - Prevents untrusted remote callers from manipulating swap state machines.
- **Reorg Resilience Regression Suite:**
  - Executed `swap/reorg_swap_01c_selftest.py` (15 tests passed):
    - `FIVE_EXPLICIT_TX_STATES=PASS`
    - `TERMINAL_EXACT_TX_OBSERVATION=PASS`
    - `REPEATED_REORG_AFTER_RECONFIRMATION=PASS`
    - `OVERLAY_REOPEN_DURABILITY=PASS`
  - Executed `swap/reorg_exit_01c_selftest.py` (all tests passed):
    - `EXPLICIT_EXECUTION_GATE_REQUIRED=PASS`
    - `EXACT_SAME_TX_ONLY=PASS`
    - `DURABLE_INTENT_BEFORE_NETWORK_MUTATOR=PASS`

---

### 6. Mobile PWA & Browser Mining (`06_pwa_mobile_miner_test.py`)
- **Objective:** Verify mobile browser mining via restricted gateway RPC.
- **Browser Work Payload:**
  - Call: `getblocktemplate({"browserMinerAddress": "TQWoB1FwWSFp5hDcFV5FzNvQG6kne2sxJr"})`
  - Output: `browserWork` with canonical `TRU-WEB-MINER-01` candidate.
  - Coinbase output directs 50.0+ TRU block reward to the browser miner's address.
- **WebAssembly Performance Benchmark:**
  - Evaluated double-SHA256 loop: computed 50,000 nonces in 0.024s (~2.11 MH/s).
  - Formatted candidate submission payload matching `handleSubmitBlockOptimized`:
    ```json
    {
      "browserCandidate": "<serialized_block>",
      "nonce": 37038
    }
    ```

---

## 🚀 How to Run the Tests

From the repository root:

```bash
# Execute the full test suite in one command:
./community_tests/run_all.sh

# Or run individual feature tests:
python3 community_tests/01_truscriptions_test.py
python3 community_tests/02_smart_contracts_test.py
python3 community_tests/03_token_evolution_test.py
python3 community_tests/04_web_wallet_backup_test.py
python3 community_tests/05_swap_htlc_test.py
python3 community_tests/06_pwa_mobile_miner_test.py
```

All test runs produce standalone JSON artifacts in `community_tests/*_result.json`.

