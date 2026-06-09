from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass


BASE_CHAIN_ID = 8453
DEX_NAME = "Sector One"
ROUTER_ADDRESS = "0xd4f937581650A2d6e416Dd9EF5372C1672422843"
POOL_ADDRESS = "0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b"
TOKEN_X_SYMBOL = "WETH"
TOKEN_X_ADDRESS = "0x4200000000000000000000000000000000000006"
TOKEN_X_DECIMALS = 18
TOKEN_Y_SYMBOL = "USDC"
TOKEN_Y_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
TOKEN_Y_DECIMALS = 6
BIN_STEP = 4

# Refresh live active bin via discover_lb_pool.py before execution.
HISTORICAL_ACTIVE_BIN_ID = 8369121


@dataclass
class DepositPlan:
    chain_id: int
    dex_name: str
    router_address: str
    pool_address: str
    token_x_symbol: str
    token_x_address: str
    token_y_symbol: str
    token_y_address: str
    bin_step: int
    active_bin_id: int
    active_bin_source: str
    amount_x_raw: int
    amount_y_raw: int
    amount_x_min_raw: int
    amount_y_min_raw: int
    delta_ids: list[int]
    distribution_x: list[int]
    distribution_y: list[int]
    to: str
    refund_to: str
    deadline: int
    method: str
    value_wei: int


def to_raw(amount: float, decimals: int) -> int:
    return int(round(amount * (10 ** decimals)))


def centered_bins(active_bin_id: int, total_bins: int) -> list[int]:
    if total_bins <= 0:
        raise ValueError("total_bins must be > 0")
    left = total_bins // 2
    right = total_bins - left - 1
    return list(range(active_bin_id - left, active_bin_id + right + 1))


def build_centered_distributions(bin_ids: list[int], active_bin_id: int) -> tuple[list[int], list[int], list[int]]:
    total_supply = int(1e18)
    num_bins = len(bin_ids)
    delta_ids = [bin_id - active_bin_id for bin_id in bin_ids]
    distribution_x = [0] * num_bins
    distribution_y = [0] * num_bins

    center_index = bin_ids.index(active_bin_id)
    bins_below = [b for b in bin_ids if b < active_bin_id]
    bins_above = [b for b in bin_ids if b > active_bin_id]
    num_left_bins = len(bins_below)
    num_right_bins = len(bins_above)

    center_share = total_supply // num_bins
    distribution_x[center_index] = center_share
    distribution_y[center_index] = center_share

    if num_right_bins > 0:
        x_side_share = (total_supply - center_share) // num_right_bins
        for i in range(center_index + 1, num_bins):
            distribution_x[i] = x_side_share
        used_x = center_share + (x_side_share * num_right_bins)
        distribution_x[-1] += (total_supply - used_x)

    if num_left_bins > 0:
        y_side_share = (total_supply - center_share) // num_left_bins
        for i in range(center_index):
            distribution_y[i] = y_side_share
        used_y = center_share + (y_side_share * num_left_bins)
        distribution_y[center_index - 1] += (total_supply - used_y)

    distribution_x[-1] += total_supply - sum(distribution_x)
    distribution_y[center_index] += total_supply - sum(distribution_y)

    return delta_ids, distribution_x, distribution_y


def build_plan(
    *,
    sender: str,
    amount_weth: float,
    amount_usdc: float,
    total_bins: int = 50,
    slippage_percent: float = 0.5,
    active_bin_id: int = HISTORICAL_ACTIVE_BIN_ID,
    spend_native_for_weth_side: bool = False,
) -> DepositPlan:
    bin_ids = centered_bins(active_bin_id, total_bins)
    delta_ids, distribution_x, distribution_y = build_centered_distributions(bin_ids, active_bin_id)

    amount_x_raw = to_raw(amount_weth, TOKEN_X_DECIMALS)
    amount_y_raw = to_raw(amount_usdc, TOKEN_Y_DECIMALS)
    amount_x_min_raw = int(amount_x_raw * (1 - slippage_percent / 100))
    amount_y_min_raw = int(amount_y_raw * (1 - slippage_percent / 100))
    deadline = int(time.time()) + 300

    method = "addLiquidityNATIVE" if spend_native_for_weth_side else "addLiquidity"
    value_wei = amount_x_raw if spend_native_for_weth_side else 0

    return DepositPlan(
        chain_id=BASE_CHAIN_ID,
        dex_name=DEX_NAME,
        router_address=ROUTER_ADDRESS,
        pool_address=POOL_ADDRESS,
        token_x_symbol=TOKEN_X_SYMBOL,
        token_x_address=TOKEN_X_ADDRESS,
        token_y_symbol=TOKEN_Y_SYMBOL,
        token_y_address=TOKEN_Y_ADDRESS,
        bin_step=BIN_STEP,
        active_bin_id=active_bin_id,
        active_bin_source="historical_snapshot_refresh_required",
        amount_x_raw=amount_x_raw,
        amount_y_raw=amount_y_raw,
        amount_x_min_raw=amount_x_min_raw,
        amount_y_min_raw=amount_y_min_raw,
        delta_ids=delta_ids,
        distribution_x=distribution_x,
        distribution_y=distribution_y,
        to=sender,
        refund_to=sender,
        deadline=deadline,
        method=method,
        value_wei=value_wei,
    )


def main() -> None:
    sender = "0xYourWalletHere"
    plan = build_plan(
        sender=sender,
        amount_weth=0.0243,
        amount_usdc=91.36,
        total_bins=50,
        slippage_percent=0.5,
        active_bin_id=HISTORICAL_ACTIVE_BIN_ID,
        spend_native_for_weth_side=False,
    )
    print(json.dumps(asdict(plan), indent=2))


if __name__ == "__main__":
    main()
