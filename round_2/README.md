# TRU Community Tests — Round 2

Welcome to **Round 2** of the Tokenized Real Utility (TRU) Community Test Suite.

## Overview
Following the acceptance of Round 1 by TRU Core Head Dev, Round 2 targets:
1. **Core 0.05 Network Resilience**: Automatic verified-peer recovery (`[PEER-REDIAL-01]`), exponential backoff, table poisoning prevention.
2. **Bounded Log Rotation Under Load**: Production logging, 32 MiB hard rotation limit, 4-tier archive retention, zero disk runaway.
3. **Smart Contract VM Bounds**: Gas exhaustion (`MAX_TX_SCRIPT_GAS`), opcode limits, SigOps caps, CLTV MTP rollback safety.
4. **Living Token Evolution (SFT)**: Split-brain resistance, unauthorized mutation rejection, epoch sequence monotonicity.
5. **Mempool & Cryptographic Edge Cases**: Dust limits, double-spend eviction, BIP62 Low-S signature malleability, zero-disclosure DID validation.

## Master Specification & Test Plan
See the full specification and test definitions in:
👉 **[ROUND_2_TEST_PLAN.md](ROUND_2_TEST_PLAN.md)**

## Safety Notice
As requested by Head Dev (#348):
> *"One good habit for any test suite: use a fresh test wallet with a small balance, never your main keys."*
All tests in this suite operate exclusively with ephemeral test wallets.
