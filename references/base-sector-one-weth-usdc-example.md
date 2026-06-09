# Base Sector One WETH-USDC Example

Fully grounded Base-chain example using live SectorOne API data (as of integration).

## Example identity

- **Chain**: Base
- **Chain ID**: `8453`
- **DEX**: Sector One
- **Protocol family**: Liquidity Book / DLMM (Joe 2.0)
- **LB Router v2.0**: `0xd4f937581650A2d6e416Dd9EF5372C1672422843`
- **Pool contract** (top liquidity WETH-USDC, binStep 4): `0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b`
- **Pool name**: `WETH-USDC`
- **binStep**: `4`
- **lbVersion** (API): `v21` (app fee mode — not v2.1 factory)

## Token details

### token_x (WETH)
- **address**: `0x4200000000000000000000000000000000000006`
- **decimals**: `18`

### token_y (USDC)
- **address**: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- **decimals**: `6`

## Discovery command

```bash
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --token-x WETH --token-y USDC \
  --bin-step 4 \
  --rpc-url https://base-rpc.publicnode.com
```

Always use the returned `active_bin_id` — do not hardcode.

## Deposit methods

| User intent | Router method |
| --- | --- |
| ERC-20 WETH + USDC | `addLiquidity` |
| Native ETH + USDC | `addLiquidityNATIVE` |

## App deep link

```text
https://app.sectorone.xyz/liquidity/manual/:8453/add/v20/0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b/4
```

## ABIs

- Router: `references/liquidity-book-router-minimal-abi.json`
- ERC-20: `references/erc20-minimal-abi.json`
- Pair: `references/lb-pair-minimal-abi.json`

## External docs

- https://docs.sectorone.xyz/
- https://github.com/DoctorTangle/Sectoroneskills
