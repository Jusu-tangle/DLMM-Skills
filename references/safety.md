# SectorOne Safety Reference

## Scope

- **Base mainnet** (`8453`) is the primary execution chain.
- Unsigned calldata only — no private keys, no local signing unless the user explicitly uses their own wallet stack.

## Transaction flow

1. Build unsigned calldata (Python scripts or dlmmskills CLI).
2. Simulate when possible.
3. User approves and signs in wallet (Base Account, Bankr, or browser wallet).

## Approvals

- **Add liquidity:** approve each ERC-20 leg to the LB router before the router call.
- **Remove liquidity:** `setApprovalForAll(router, true)` on the LB pair may be required before router withdrawal.
- **Native ETH:** use `addLiquidityNATIVE` / `removeLiquidityNATIVE`; supply ETH as transaction `value`.

## Slippage

- Default in Python scripts: **0.5%** (`--slippage-percent 0.5`).
- Warn on elevated slippage for thin pools.
- Rebuild calldata if the active bin moves materially before execution.

## Deadlines

- Python scripts use **300 seconds** TTL. Rebuild if the user waits past the deadline.

## Protocol versions

- **LB v2.0** is the default on Base.
- **v2.2** only for pools on the v2.2 factory.
- **v2.1 factory is not on Base.**

## Liquidity risks

- DLMM liquidity is **bin-local** — wrong bin range can leave capital idle.
- Always refresh `active_bin_id` via RPC before spot-centered deposits.
- Before remove, confirm bin IDs and LP amounts.

## User approval

Show summary (amounts, pool, bin range, slippage) before any live send.
