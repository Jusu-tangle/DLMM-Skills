# Sector One WETH-USDT0 Example

This example is based on the current local Sector One toolkit and integration docs.

Unlike the Base Sector One WETH-USDC example, the repo does **not** contain a committed Sector One pool-address fixture or active-bin snapshot for `WETH-USDT0`.

That means this example is still useful and mostly complete, but:

- the **router address is known**
- the **token addresses are known**
- the **bin step pattern is known**
- a **repo-local example pool address exists**
- the **live active bin must still be refreshed from the live API / chain**

## Example identity

- **Chain**: MegaETH
- **Chain ID**: `4326`
- **DEX**: Sector One
- **Protocol family**: Liquidity Book / DLMM
- **Router contract**: `0xd02bECF89D2670BAB93B738697Fa4D59B4f57B5E`
- **Example pool contract**: `0x341dc63fFCcF561214405c13c22abc81EFFBdf99`
- **Example pair**: `WETH-USDT0`
- **Suggested binStep**: `10`

## Token details

### token_x
- **symbol**: `WETH`
- **address**: `0x4200000000000000000000000000000000000006`
- **decimals**: `18`

### token_y
- **symbol**: `USDT0`
- **address**: `0xb8ce59fc3717ada4c02eadf9682a9e934f625ebb`
- **decimals**: `6`

## What is confirmed from current source

The local standalone `sector_one_x/` toolkit confirms:

- Sector One uses an **LBRouter**-style flow
- swap examples use:
  - `token_in`
  - `token_out`
  - `amount_in_raw`
  - `min_amount_out_raw`
  - `bin_step`
  - `simulate=True|False`
- the toolkit expects the LBRouter ABI from:
  - `abi/lbrouter_contract_abi.json`

## What still must be refreshed live

Before constructing a live deposit:

1. confirm the current `WETH-USDT0` pool address still matches the live API / chain
2. confirm `binStep`
3. refresh the current `active_bin_id`

You can do that through:

- a Sector One API client / price fetcher
- a pool search by token pair
- a block explorer or chain query

## Deposit method choice

### If user deposits wrapped WETH as an ERC-20
Use:

- `addLiquidity(LiquidityParameters)`

### If user wants to spend native ETH on the WETH side
Use:

- `addLiquidityNATIVE(LiquidityParameters)`

In that case:

- keep `tokenX` as the wrapped native token address in the struct
- send the native amount as transaction value
- approve only the non-native ERC-20 side

## ABI guidance

Use the toolkit references:

- `references/liquidity-book-router-minimal-abi.json`
- `references/erc20-minimal-abi.json`

## Recommended execution order

1. confirm router address and ABI
2. resolve live pool address for `WETH-USDT0`
3. confirm `binStep`
4. refresh `active_bin_id`
5. convert human amounts to raw units
6. derive centered or explicit bin layout
7. derive `deltaIds`, `distributionX`, `distributionY`
8. plan token approval(s)
9. build calldata
10. simulate
11. only then send

## Local source notes

Repo-backed:

- `sector_one_x/START_HERE.md`
- `sector_one_x/README.md`
- `sector_one_x/TRADING_GUIDE.md`
- `sector_one_x/swapper.py`
- `sector_one_x/example_swap.py`
- `docs/plans/megaeth_sector_one_integration.md`
- `liquidity_async/market_data/sources/sector_one.py`

## Key limitation

This example is **router-complete but active-bin-incomplete**.

That is still enough for a practical toolkit because the router call shape is stable, but Bankr should:

- treat pool confirmation as a live discovery step
- refuse to finalize a spot-centered deposit until `active_bin_id` is refreshed
