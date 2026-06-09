# Bankr handoff (SectorOne skills)

SectorOne skills **never contain API keys**. Execution is delegated to the core **`bankr` skill**.

## Install on a Bankr bot

```bash
# 1. Bankr wallet + submit (once per bot)
npx skills add BankrBot/skills --skill bankr

# 2. SectorOne domain skills
npx skills add <your-repo> --skill liquidity-planner
npx skills add <your-repo> --skill sectorone-execute
```

Configure the API key on the **bot host** only (`bankr login --read-write` or `BANKR_API_KEY` in env). Not in skill markdown.

## Division of labor

| Skill | Role |
| --- | --- |
| `bankr` | Wallet, balances, `wallet submit`, auth |
| `liquidity-planner` | Explain DLMM, deep links, planning |
| `sectorone-execute` | Build `calls[]` via Python, hand off to `bankr` |

## Submit shape

Each call in `calls[]`:

```json
{
  "to": "0xContract",
  "data": "0xCalldata",
  "value": "0x0",
  "label": "human-readable step name"
}
```

Hand to bankr skill as:

```text
Submit on Base (chainId 8453): to=0x..., data=0x..., value=0x0
```

Or CLI:

```bash
bankr wallet submit --to 0x... --data 0x... --value 0x0 --chain base --wait
```

(Exact CLI flags — follow the bankr skill reference.)

## Deposit call order

1. ERC-20 `approve` for each token leg (if not using native ETH path)
2. Router `addLiquidity` or `addLiquidityNATIVE` (`value` = ETH wei for native path)

## Withdraw call order

1. LB pair `approveForAll(router, true)` — skip if already approved
2. Router `removeLiquidity` or `removeLiquidityNATIVE`

## Rules

1. Show `summary` before submit.
2. User must confirm.
3. Sequential submit with confirmation between steps.
4. Stop on first error.
5. Read-write API key required (`--read-write` at login).

## Python scripts with `--bankr-format`

| Script | Purpose |
| --- | --- |
| `discover_lb_pool.py` | Pool + active bin |
| `read_lb_position.py` | Bin IDs + LP amounts for withdraw |
| `build_lb_add_liquidity_calldata.py --bankr-format` | Deposit `calls[]` |
| `build_lb_remove_liquidity_calldata.py --bankr-format` | Withdraw `calls[]` |
