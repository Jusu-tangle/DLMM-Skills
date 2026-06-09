---
name: sectorone-dlmm
description: SectorOne DLMM on Base — discover pools, plan swaps and liquidity, build add/remove calldata with Python scripts, or escalate to dlmmskills CLI for swaps and Base MCP. Use for SectorOne / Joe Liquidity Book on Base (8453) and MegaETH (4326) pool discovery.
tags:
  - dlmm
  - liquidity-book
  - sectorone
  - base
  - swaps
  - liquidity
version: 2.0.0
visibility: private
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Bash
  - WebFetch
  - WebSearch
license: MIT
metadata:
  author: generic-dllm-driver
  version: 2.0.0
---

# SectorOne DLMM Driver

Unified skill for **SectorOne** (Liquidity Book / DLMM) on **Base mainnet** (`8453`). Includes Bankr-safe planners, Python calldata builders with **Bankr handoff** (`--bankr-format`), and escalation to [dlmmskills](https://github.com/DoctorTangle/dlmmskills) for swaps.

> **Bankr bots:** Install `bankr` + `sectorone-execute` + `liquidity-planner`. No API keys in SectorOne skills — see [docs/BANKR.md](docs/BANKR.md).

> **SectorOne on Base** is the same protocol formerly branded Swapline. Use SectorOne naming, API (`api.sectorone.xyz`), and router addresses from [references/addresses.md](references/addresses.md).

## When to use

| User asks | Path |
| --- | --- |
| Swap on SectorOne (human executes in app) | [skills/swap-planner/SKILL.md](skills/swap-planner/SKILL.md) |
| Add/remove LP (plan + app link) | [skills/liquidity-planner/SKILL.md](skills/liquidity-planner/SKILL.md) |
| **Deposit/withdraw LP with Bankr wallet** | [skills/sectorone-execute/SKILL.md](skills/sectorone-execute/SKILL.md) → hands off to **`bankr` skill** |
| Find pool / active bin / inspect pool | `scripts/discover_lb_pool.py` |
| Read LP bins for withdraw | `scripts/read_lb_position.py` |
| Build add/remove calldata | `scripts/build_lb_*_calldata.py` (add `--bankr-format` for Bankr) |
| Exact swap quote / swap calldata | **dlmmskills CLI** — see [docs/BANKR.md](docs/BANKR.md) |
| Base MCP `send_calls` | dlmmskills CLI + Base MCP |

## Quick start (Python calldata path)

```bash
pip install -r requirements.txt

# 1. Discover pool + refresh active bin
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --token-x WETH --token-y USDC \
  --rpc-url https://base-rpc.publicnode.com

# 2. Build add-liquidity calldata (use active_bin from step 1)
python scripts/build_lb_add_liquidity_calldata.py \
  --preset base_sector_one_weth_usdc \
  --sender 0xYourWallet \
  --amount-x 0.01 --amount-y 30 \
  --active-bin <FROM_DISCOVERY> \
  --total-bins 50
```

See [USAGE.md](USAGE.md) for full commands.

## Default protocol version (Base)

- **LB v2.0 (Joe 2.0)** — default; router `0xd4f937581650A2d6e416Dd9EF5372C1672422843`
- **LB v2.2** — only for v2.2-factory pools; router `0x87aC1EB5596D47f6fd7d0D17bEE233783dB5CfEC`
- **v2.1 factory is not on Base**

## Reference docs

| File | Purpose |
| --- | --- |
| [references/chains.md](references/chains.md) | Chain IDs, RPC, routers, tokens |
| [references/addresses.md](references/addresses.md) | Contract addresses |
| [references/dlmm-bins.md](references/dlmm-bins.md) | Bin step, active bin, LP concepts |
| [references/deep-links.md](references/deep-links.md) | app.sectorone.xyz URLs |
| [references/data-providers.md](references/data-providers.md) | API + RPC sources |
| [references/safety.md](references/safety.md) | Slippage, approvals, risks |
| [docs/BANKR.md](docs/BANKR.md) | Bankr vs CLI escalation |

## Workflow decision tree

```
User request
├── Swap only, no calldata needed
│   └── swap-planner → deep link
├── LP plan only, no calldata needed
│   └── liquidity-planner → deep link
├── Need pool metadata / active bin
│   └── discover_lb_pool.py
├── Need add/remove LP calldata (Python)
│   ├── discover pool + active bin
│   ├── build_lb_add_liquidity_calldata.py OR build_lb_remove_liquidity_calldata.py
│   └── simulate → user signs
└── Need swap calldata / read-position / create pool
    └── dlmmskills CLI (npm install required)
```

## Safety rules

- Refresh **live active bin** before spot-centered deposits — never trust historical snapshots.
- Check ERC-20 **approvals** to the correct router before LP actions.
- **Simulate** before live send when a simulation path exists.
- Do not guess router version — match pool `lbVersion` / factory.
- Scripts **do not send transactions** — they output JSON plans with `calldata`.

## MegaETH support

Pool discovery and calldata presets exist for MegaETH (`--source sector_one`, preset `sector_one_weth_usdt0`). Base is the primary, fully documented chain.

## Success condition

A concrete plan that names the action path, required inputs, pool/router context, risks (stale bin, thin liquidity), and the next execution step (app link, calldata JSON, or CLI command).
