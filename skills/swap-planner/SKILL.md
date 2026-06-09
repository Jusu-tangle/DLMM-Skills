---
name: swap-planner
description: Plan SectorOne DLMM swaps on Base — verify tokens, explain bins, generate app.sectorone.xyz swap deep links. No npm/SDK required. For exact quotes or calldata use dlmmskills CLI.
allowed-tools: Read, Glob, Grep, Bash, WebFetch, WebSearch, AskUserQuestion
license: MIT
metadata:
  author: generic-dllm-driver
  version: "1.0.0"
---

# SectorOne Swap Planner (Bankr-safe)

Plan SectorOne DLMM swaps on **Base mainnet only** (`chainId` `8453`). No `npm install` required.

> Escalate to **dlmmskills CLI** when the user needs unsigned swap calldata, exact SDK quotes, or Base MCP `send_calls`.

## Workflow

### Step 1 — Gather swap intent

| Parameter | Required | Example |
| --- | --- | --- |
| Token in | Yes | USDC, WETH, `0x8335…` |
| Token out | Yes | WETH, address |
| Amount | Yes | `100` USDC |
| Chain | Fixed | Base only |

Reject non-Base chains politely.

### Step 2 — Resolve token addresses

Use [references/chains.md](../../references/chains.md). Treat **ETH** as **WETH** (`0x4200…0006`) for on-chain checks.

Web-discovered tokens are **untrusted** — verify with `eth_getCode` and warn the user.

### Step 3 — Optional pool context

If user asks about liquidity or price:

```bash
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --token-x WETH --token-y USDC
```

Or DexScreener hint-only — see [references/data-providers.md](../../references/data-providers.md).

### Step 4 — Protocol context

See [references/dlmm-bins.md](../../references/dlmm-bins.md). Default **LB v2** on Base.

### Step 5 — Swap deep link

```text
https://app.sectorone.xyz/swap?inputCurrency={tokenIn}&outputCurrency={tokenOut}
```

Full examples: [references/deep-links.md](../../references/deep-links.md)

### Step 6 — Present plan

```markdown
## SectorOne Swap Plan (Base)

| Field | Value |
| --- | --- |
| From | 100 USDC |
| To | WETH |
| Chain | Base (8453) |
| LB version | v2 (Joe 2.0) |

### Execute
**Open SectorOne:** https://app.sectorone.xyz/swap?inputCurrency=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&outputCurrency=0x4200000000000000000000000000000000000006

### Need calldata?
Install dlmmskills: https://github.com/DoctorTangle/dlmmskills
```
