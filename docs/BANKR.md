# Bankr Bot Setup

Best-practice layout for running SectorOne DLMM on a **Bankr bot** — matching the Uniswap driver/trading split.

## Install these skills

```bash
# Bankr core — wallet + submit (API key configured on bot host, NOT in skills)
npx skills add BankrBot/skills --skill bankr

# SectorOne — planning (no execution)
npx skills add <your-repo> --skill liquidity-planner
npx skills add <your-repo> --skill swap-planner

# SectorOne — deposit/withdraw execution (hands off to bankr skill)
npx skills add <your-repo> --skill sectorone-execute
```

On the bot host:

```bash
bankr login --api-key bk_YOUR_KEY   # or bankr login email ... --read-write
pip install -r requirements.txt     # if shell + Python available
```

## Which skill when?

| User goal | Skill | Executes on-chain? |
| --- | --- | --- |
| Plan LP, open app | `liquidity-planner` | No (deep link) |
| Plan swap, open app | `swap-planner` | No (deep link) |
| **Deposit LP with Bankr wallet** | `sectorone-execute` | Yes (via `bankr` skill) |
| **Withdraw LP with Bankr wallet** | `sectorone-execute` | Yes (via `bankr` skill) |
| Swap with Bankr wallet | Not covered — use app or dlmmskills | — |

## How execution works

```
sectorone-execute          bankr skill
       │                        │
       ├─ discover pool         │
       ├─ build calls[]         │
       ├─ show summary          │
       └─ user confirms ───────► wallet submit (per call, in order)
```

**SectorOne skills do not call the Bankr API directly.** They output `calls[]`; the `bankr` skill submits them.

## Deposit example (agent workflow)

1. `discover_lb_pool.py` → pool + `active_bin_id`
2. `build_lb_add_liquidity_calldata.py --bankr-format` → `calls[]`
3. Show `summary` to user → get confirmation
4. For each call in `calls[]`: use **bankr skill** to submit on Base (8453)

## Withdraw example

1. `discover_lb_pool.py` → pool + `active_bin_id`
2. `read_lb_position.py` → bin IDs + LP amounts
3. `build_lb_remove_liquidity_calldata.py --bankr-format` → `calls[]`
4. Confirm with user (especially for 100% withdraw)
5. Submit via **bankr skill** in order

## What Bankr bot needs

| Requirement | Why |
| --- | --- |
| `bankr` skill + read-write API key | Submit transactions |
| `sectorone-execute` skill | Build SectorOne calldata |
| Python 3 + `pip install -r requirements.txt` | Run local scripts |
| Shell access on bot host | Run Python scripts |

If the bot has **no shell**, use `liquidity-planner` only (app deep links).

## What is NOT in SectorOne skills

- No `BANKR_API_KEY` in markdown
- No curl recipes with embedded keys
- No duplicate Bankr submit API docs (reference `bankr` skill instead)

See [references/bankr-handoff.md](../references/bankr-handoff.md).

## Optional: dlmmskills

For swap calldata, pool creation, or SDK-exact layouts:

```bash
git clone https://github.com/DoctorTangle/dlmmskills.git && cd dlmmskills && npm install
```

Still submit via the **bankr** skill — dlmmskills only builds `calls[]`.
