# SectorOne DLMM Driver Toolkit

Agent skills for **SectorOne** DLMM on **Base**, designed for **Bankr bots**.

## Bankr bot install (recommended)

```bash
# Core Bankr — API key on bot host only, never in skills
npx skills add BankrBot/skills --skill bankr

# SectorOne skills from this repo
npx skills add <your-repo> --skill liquidity-planner
npx skills add <your-repo> --skill swap-planner
npx skills add <your-repo> --skill sectorone-execute
```

```bash
pip install -r requirements.txt   # on bot host if shell available
```

Full setup: [docs/BANKR.md](docs/BANKR.md)

## Skill map

| Skill | Purpose | On-chain? |
| --- | --- | --- |
| `liquidity-planner` | Plan LP, app deep links | No |
| `swap-planner` | Plan swaps, app deep links | No |
| `sectorone-execute` | Deposit/withdraw via Bankr wallet | Yes (via `bankr` skill) |
| `bankr` (external) | Wallet + submit | Yes |

## What you can do

| Action | How |
| --- | --- |
| Plan LP + app link | `liquidity-planner` |
| **Deposit LP with Bankr** | `sectorone-execute` → `--bankr-format` → `bankr` skill submit |
| **Withdraw LP with Bankr** | `sectorone-execute` → `read_lb_position.py` → `--bankr-format` → `bankr` skill |
| Discover pools | `discover_lb_pool.py` |

## Quick start (deposit via Bankr)

```bash
# 1. Discover
python scripts/discover_lb_pool.py --source sector_one_base \
  --token-x WETH --token-y USDC --rpc-url https://base-rpc.publicnode.com

# 2. Build Bankr-ready calls (use Bankr wallet as --sender)
python scripts/build_lb_add_liquidity_calldata.py \
  --preset base_sector_one_weth_usdc --sender 0xBankrWallet \
  --amount-x 0.01 --amount-y 30 --active-bin <ID> --bankr-format

# 3. Submit each call in calls[] via bankr skill
```

See [USAGE.md](USAGE.md) and [references/bankr-handoff.md](references/bankr-handoff.md).

## Still needs dlmmskills

- Swap quotes and swap calldata
- Pool creation
- SDK-exact layouts (optional alternative to Python scripts)

## License

MIT
