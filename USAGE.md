# SectorOne DLMM Driver — Usage Examples

```bash
pip install -r requirements.txt
```

## 1. Discover a Base Sector One pool

### By token pair (highest liquidity match)

```bash
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --token-x WETH \
  --token-y USDC
```

### With live active bin refresh

```bash
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --token-x WETH \
  --token-y USDC \
  --bin-step 4 \
  --rpc-url https://base-rpc.publicnode.com
```

### By pool address

```bash
python scripts/discover_lb_pool.py \
  --source sector_one_base \
  --pool-address 0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b \
  --rpc-url https://base-rpc.publicnode.com
```

## 2. Discover a MegaETH pool

```bash
python scripts/discover_lb_pool.py \
  --source sector_one \
  --token-x WETH \
  --token-y USDT0 \
  --bin-step 10 \
  --rpc-url https://mainnet.megaeth.com/rpc
```

## 3. Build add-liquidity calldata

Use `active_bin_id` from discovery output. Use your **Bankr Base wallet** as `--sender` for Bankr execution.

```bash
python scripts/build_lb_add_liquidity_calldata.py \
  --preset base_sector_one_weth_usdc \
  --sender 0xYourBankrWallet \
  --amount-x 0.01 \
  --amount-y 30 \
  --active-bin 12345678 \
  --total-bins 50 \
  --slippage-percent 0.5
```

### Bankr-ready output (for sectorone-execute skill)

Add `--bankr-format` to get ordered `calls[]` for handoff to the **bankr** skill:

```bash
python scripts/build_lb_add_liquidity_calldata.py \
  --preset base_sector_one_weth_usdc \
  --sender 0xYourBankrWallet \
  --amount-x 0.01 --amount-y 30 \
  --active-bin 12345678 \
  --bankr-format
```

### Native ETH on WETH side

```bash
python scripts/build_lb_add_liquidity_calldata.py \
  --preset base_sector_one_weth_usdc \
  --sender 0xYourWalletHere \
  --amount-x 0.01 \
  --amount-y 30 \
  --active-bin 12345678 \
  --total-bins 50 \
  --spend-native-for-x-side
```

## 4. Read LP position (for withdraw)

```bash
python scripts/read_lb_position.py \
  --pool-address 0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b \
  --wallet 0xYourBankrWallet \
  --rpc-url https://base-rpc.publicnode.com \
  --active-bin 8338606 \
  --total-bins 50
```

## 5. Build remove-liquidity calldata

Use bin IDs and `lp_amount` values from `read_lb_position.py`.

```bash
python scripts/build_lb_remove_liquidity_calldata.py \
  --preset base_sector_one_weth_usdc \
  --sender 0xYourBankrWallet \
  --ids 8369118,8369119,8369120 \
  --amounts 1000,1000,1000 \
  --withdraw-percent 100 \
  --bankr-format
```

## 6. Submit via Bankr

Do **not** call the Bankr API from SectorOne skills. Hand `calls[]` to the **bankr** skill:

```text
Submit on Base (chainId 8453): to=0x..., data=0x..., value=0x0
```

See [references/bankr-handoff.md](references/bankr-handoff.md) and [docs/BANKR.md](docs/BANKR.md).

## 7. App deep links (no scripts)

**Swap:** `https://app.sectorone.xyz/swap?inputCurrency=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&outputCurrency=0x4200000000000000000000000000000000000006`

**Add LP:** `https://app.sectorone.xyz/liquidity/manual/:8453/add/v20/0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b/4`

See [references/deep-links.md](references/deep-links.md).

## 8. Recommended workflow

1. Discover or confirm the pool (`discover_lb_pool.py`)
2. Refresh active bin via `--rpc-url`
3. Build calldata
4. Verify ERC-20 approvals to router `0xd4f937581650A2d6e416Dd9EF5372C1672422843`
5. Simulate
6. User signs and sends

## 9. Escalation to dlmmskills (swaps only)

```bash
git clone https://github.com/DoctorTangle/dlmmskills.git
cd dlmmskills && npm install
export BASE_RPC_URL="https://base-rpc.publicnode.com"
npm run sectorone -- quote --help
```

See [docs/BANKR.md](docs/BANKR.md).
