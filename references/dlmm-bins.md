# DLMM bins on SectorOne (Base)

SectorOne uses **Liquidity Book (LB / DLMM)** — liquidity lives in discrete **price bins**, not Uniswap-style tick ranges.

## Core concepts

| Term | Meaning |
| --- | --- |
| **Bin** | Price bucket; swaps move the **active bin** as liquidity is consumed |
| **Bin step** | Spacing between bins (basis points). Same token pair can have multiple pools with different bin steps |
| **Active bin** | Current trading price bin; swap slippage depends on depth **in and around** this bin |
| **LB version** | Factory/router generation — on Base, **v2 (Joe 2.0)** holds most liquidity |

## LB versions on Base

| Version | When to use | Router (see chains.md) |
| --- | --- | --- |
| **v2** (Joe 2.0) | Default — most pairs | LB Router v2.0 |
| **v22** (v2.2 factory) | Only if user/pool is explicitly v2.2 | LB Router v2.2 |
| **v2.1** | **Not deployed on Base** | — |

When unsure, recommend **v2** and tell the user to confirm the pool in the app.

## Bin step selection (planning guide)

| Bin step | Typical use | Trade-off |
| --- | --- | --- |
| Lower (e.g. 1–10) | Stable or correlated pairs | Tighter bins, more active management |
| Medium (e.g. 20–50) | Major pairs (WETH/USDC) | Common default range |
| Higher (e.g. 80–100) | Volatile / memecoins | Wider effective steps, less precision |

**Planner cannot pick the exact bin step without on-chain pool data.** Use `scripts/discover_lb_pool.py` or ask the user which pool they use in the app.

## Add liquidity (user flow)

1. Choose token pair on **Base** in SectorOne app
2. Select pool / **bin step**
3. Choose **price range** as bin IDs or visual range in UI
4. Deposit token X and/or Y — ratio depends on active bin vs selected range
5. Confirm in app (user wallet signs)

## Remove liquidity

Removing LP requires knowing **which bins** hold the user's position.

| Surface | Capability |
| --- | --- |
| SectorOne app deep link | `…/liquidity/manual/:8453/remove/v20/{pair}/{binStep}` — see [deep-links.md](deep-links.md) |
| This toolkit (Python) | `build_lb_remove_liquidity_calldata.py` with bin IDs + amounts |
| dlmmskills CLI | `read-position` → `build-remove-liquidity` with `--bin-ids` |

## Impermanent loss / range risk

- If price moves **outside** deposited bins, the position stops earning fees and may be 100% one token
- Narrower bin ranges → higher fee capture when in range, more rebalance risk
- Warn on volatile pairs and large single-sided deposits
