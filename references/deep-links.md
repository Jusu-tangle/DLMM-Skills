# SectorOne app deep links

Base app: **https://app.sectorone.xyz**

## Add liquidity (manual DLMM)

```text
https://app.sectorone.xyz/liquidity/manual/:8453/add/v20/{lbPairAddress}/{binStep}
```

Example:

```text
https://app.sectorone.xyz/liquidity/manual/:8453/add/v20/0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b/4
```

| Segment | Value | Notes |
| --- | --- | --- |
| `chainId` | `8453` | Base mainnet — literal `:8453` in path |
| action | `add` | Manual add-liquidity flow |
| `lbAppVersion` | `v20` | Default for Joe 2.0 pools on Base |
| `lbPairAddress` | `0x…` | **LB pair contract** (not token address) |
| `binStep` | e.g. `4`, `10`, `25` | Must match the pair |

### Resolving `lbPairAddress` + `binStep`

| Method | When |
| --- | --- |
| User pastes app URL | Parse path segments |
| **This toolkit** | `scripts/discover_lb_pool.py --source sector_one_base …` |
| **dlmmskills CLI** | `list-pairs --token-in … --token-out … --lb-version v2 --json` |

## Remove liquidity

```text
https://app.sectorone.xyz/liquidity/manual/:8453/remove/v20/{lbPairAddress}/{binStep}
```

## Swap

```text
https://app.sectorone.xyz/swap?inputCurrency={tokenIn}&outputCurrency={tokenOut}
```

Example (USDC → WETH):

```text
https://app.sectorone.xyz/swap?inputCurrency=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&outputCurrency=0x4200000000000000000000000000000000000006
```

Amount is **not** pre-filled via URL — user enters it in the app.

## Other app links

| Flow | Example |
| --- | --- |
| Vault list (Base) | `https://app.sectorone.xyz/makervault/list/:8453` |
| Linktree | https://linktr.ee/SectorOneDEX |
