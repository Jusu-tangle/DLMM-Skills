---
name: liquidity-planner
description: Plan SectorOne DLMM liquidity on Base — explain bins, bin step, range; generate add/remove LP deep links. Bankr-safe, no API keys, no execution. For Bankr wallet deposit/withdraw use sectorone-execute instead.
allowed-tools: Read, Glob, Grep, Bash, WebFetch, WebSearch, AskUserQuestion
license: MIT
metadata:
  author: generic-dllm-driver
  version: "1.1.0"
---

# SectorOne Liquidity Planner (Bankr-safe)

Plan DLMM **liquidity positions** on **Base mainnet**. No SDK, no API keys, no on-chain execution.

> **User wants Bankr wallet to deposit/withdraw?** → escalate to **`sectorone-execute`** (requires `bankr` skill on the bot).

## Workflow

### Step 1 — Gather LP intent

| Parameter | Required | Example |
| --- | --- | --- |
| Token A / B | Yes | WETH / USDC |
| Amount | Yes | 0.1 ETH + USDC |
| Action | Yes | Add / Remove |
| Bin step | If known | 4, 10, 25 |

### Step 2 — Discover pool (optional)

```bash
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --token-x WETH --token-y USDC \
  --rpc-url https://base-rpc.publicnode.com
```

### Step 3 — Explain DLMM concepts

See [references/dlmm-bins.md](../../references/dlmm-bins.md).

### Step 4 — Deep links (default execution path)

**Add:** `https://app.sectorone.xyz/liquidity/manual/:8453/add/v20/{pair}/{binStep}`

**Remove:** `https://app.sectorone.xyz/liquidity/manual/:8453/remove/v20/{pair}/{binStep}`

See [references/deep-links.md](../../references/deep-links.md).

### Step 5 — Escalate to Bankr execution

If the user wants the **Bankr wallet** to deposit or withdraw (not the app):

→ Use **`sectorone-execute`** skill. It builds `calls[]` and hands off to the **`bankr` skill**.

Do **not** put API keys or submit curl in this planner skill.

### Step 6 — Present plan

```markdown
## SectorOne Liquidity Plan (Base)

| Field | Value |
| --- | --- |
| Action | Add liquidity |
| Pair | WETH / USDC |
| Pool | 0xf69b…3b4b |
| Bin step | 4 |

### Execute in app
https://app.sectorone.xyz/liquidity/manual/:8453/add/v20/0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b/4

### Or execute with Bankr wallet
Ask to use sectorone-execute (requires bankr skill).
```
