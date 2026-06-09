---
name: sectorone-execute
description: Use when the user wants to DEPOSIT or WITHDRAW SectorOne DLMM liquidity on Base with their Bankr wallet — "add LP on SectorOne with Bankr", "deposit liquidity SectorOne", "withdraw my SectorOne LP", "execute SectorOne liquidity". Builds unsigned calldata via local Python scripts and hands off submission to the bankr skill. Does NOT contain API keys. Requires shell + Python. For app-only planning use liquidity-planner.
allowed-tools: Read, Glob, Grep, Bash, WebFetch, WebSearch, AskUserQuestion
license: MIT
metadata:
  author: generic-dllm-driver
  version: "1.0.0"
  requires_skills:
    - bankr
---

# SectorOne Execute (Bankr handoff)

Deposit or withdraw SectorOne DLMM liquidity on **Base (8453)**. This skill **builds calldata only** and delegates signing/submission to the **`bankr` skill**.

> **No API keys in this skill.** Bankr auth lives in the bot runtime (`bankr login` / `BANKR_API_KEY` on the host).

> **Prerequisite:** The bot must also have the core **`bankr`** skill installed (`npx skills add BankrBot/skills --skill bankr`).

## When to use

| User says | Use this skill |
| --- | --- |
| Add / deposit LP on SectorOne with Bankr | Yes |
| Withdraw / remove LP on SectorOne with Bankr | Yes |
| Just plan or open the app | No → `liquidity-planner` |
| Swap on SectorOne | No → `swap-planner` (app) or dlmmskills (calldata) |

## Preflight

1. Confirm the **`bankr` skill** is available (wallet + submit).
2. Confirm **Python 3** and dependencies: `pip install -r requirements.txt`
3. Get the user's **Bankr Base wallet** via the bankr skill (`bankr wallet portfolio --chain base` or agent user lookup). Use that address as `--sender` / `--wallet`.
4. Use RPC: `https://base-rpc.publicnode.com`

## Flow A — Deposit liquidity

### Step 1 — Discover pool + active bin

```bash
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --token-x WETH --token-y USDC \
  --rpc-url https://base-rpc.publicnode.com
```

Save `pool_address`, `bin_step`, `active_bin_id`.

### Step 2 — Build Bankr-ready calls

```bash
python scripts/build_lb_add_liquidity_calldata.py \
  --preset base_sector_one_weth_usdc \
  --sender <BANKR_BASE_WALLET> \
  --amount-x 0.01 \
  --amount-y 30 \
  --active-bin <ACTIVE_BIN_ID> \
  --total-bins 50 \
  --bankr-format
```

Output includes `summary`, `calls[]`, and `bankr_handoff` instructions.

### Step 3 — Show summary + confirm

Present `summary` to the user (pair, amounts, pool, active bin, number of calls). **Do not submit without explicit confirmation.**

### Step 4 — Submit via bankr skill

For each item in `calls[]` **in order**:

1. `approve` calls first (ERC-20 approvals to router)
2. `addLiquidity` or `addLiquidityNATIVE` last

Tell the bankr skill:

```text
Submit this transaction on Base: { "to": "...", "data": "...", "value": "0x0", "chainId": 8453 }
```

Or use CLI: `bankr wallet submit` with the same fields and `waitForConfirmation: true`.

**Stop on first failure.** Log each tx hash.

---

## Flow B — Withdraw liquidity

### Step 1 — Read LP position (bin IDs + amounts)

If the user does not know their bins, scan around the live active bin:

```bash
python scripts/read_lb_position.py \
  --pool-address <POOL> \
  --wallet <BANKR_BASE_WALLET> \
  --rpc-url https://base-rpc.publicnode.com \
  --active-bin <ACTIVE_BIN_ID> \
  --total-bins 50
```

Use `positions[].bin_id` and `positions[].lp_amount` from the output.

### Step 2 — Build Bankr-ready calls

```bash
python scripts/build_lb_remove_liquidity_calldata.py \
  --preset base_sector_one_weth_usdc \
  --sender <BANKR_BASE_WALLET> \
  --ids <comma-separated bin ids> \
  --amounts <comma-separated lp amounts> \
  --withdraw-percent 100 \
  --bankr-format
```

For **full withdraw**, require explicit user confirmation before `--withdraw-percent 100`.

### Step 3 — Show summary + confirm

### Step 4 — Submit via bankr skill

Typical call order:

1. `approveForAll` on the LB **pair** contract (router as operator) — unless already approved (`--skip-operator-approval`)
2. `removeLiquidity` or `removeLiquidityNATIVE` on the router

---

## Safety rules

- Base mainnet only (`chainId` 8453).
- Refresh **active bin** before every deposit.
- Show summary and get confirmation before any submit.
- Submit calls **sequentially**; wait for confirmation between steps.
- Never embed API keys in SectorOne skills.
- Never ask for a seed phrase.
- If Python is unavailable on the bot host, fall back to `liquidity-planner` app deep links.

## Escalation

| Need | Skill / tool |
| --- | --- |
| App link only | `liquidity-planner` |
| Swap calldata | dlmmskills CLI |
| Base MCP | dlmmskills + Base MCP |

See [references/bankr-handoff.md](../../references/bankr-handoff.md) and [docs/BANKR.md](../../docs/BANKR.md).
