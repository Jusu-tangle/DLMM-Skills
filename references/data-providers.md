# Data providers

SectorOne has **no public Trading API** like Uniswap. This toolkit uses these sources.

## Priority order

| Priority | Source | Use for |
| --- | --- | --- |
| 1 | `https://api.sectorone.xyz/api/v1/pools` | Pool discovery, token metadata, liquidity |
| 2 | On-chain RPC (`eth_getCode`, `getActiveId`) | Token exists, live active bin |
| 3 | SectorOne docs API | Protocol rules, LB versions, bins |
| 4 | Known token table | WETH, USDC — see [chains.md](chains.md) |
| 5 | WebSearch | Unknown token symbols (then verify on-chain) |
| 6 | DexScreener | **Optional** hint only when user asks price/liquidity |

Do **not** rely on DexScreener for execution, exact quotes, or calldata.

## SectorOne pool API

```bash
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --token-x WETH --token-y USDC \
  --rpc-url https://base-rpc.publicnode.com
```

## SectorOne docs API

```bash
curl -sG "https://docs.sectorone.xyz/sectorone/welcome.md" \
  --data-urlencode "ask=Which LB version is default on Base mainnet?"
```

## Base RPC

Default public RPC: `https://base-rpc.publicnode.com`

## What requires dlmmskills CLI

Exact SDK swap quotes, `build-swap`, `read-position`, pool creation → [dlmmskills](https://github.com/DoctorTangle/dlmmskills) CLI. See `docs/BANKR.md`.
