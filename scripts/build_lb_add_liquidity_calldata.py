from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from web3 import Web3

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bankr_calls import calls_from_add_plan, wrap_bankr_payload


ROOT = Path(__file__).resolve().parents[1]
ROUTER_ABI_PATH = ROOT / "references" / "liquidity-book-router-minimal-abi.json"


@dataclass(frozen=True)
class Preset:
    name: str
    chain: str
    chain_id: int
    dex_name: str
    router_address: str
    token_x_symbol: str
    token_x_address: str
    token_x_decimals: int
    token_y_symbol: str
    token_y_address: str
    token_y_decimals: int
    bin_step: int
    default_active_bin_id: int | None
    pool_address: str | None
    notes: str


PRESETS: dict[str, Preset] = {
    "base_sector_one_weth_usdc": Preset(
        name="base_sector_one_weth_usdc",
        chain="base",
        chain_id=8453,
        dex_name="Sector One",
        router_address="0xd4f937581650A2d6e416Dd9EF5372C1672422843",
        token_x_symbol="WETH",
        token_x_address="0x4200000000000000000000000000000000000006",
        token_x_decimals=18,
        token_y_symbol="USDC",
        token_y_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        token_y_decimals=6,
        bin_step=4,
        default_active_bin_id=None,
        pool_address="0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b",
        notes="LB v2.0 router. Refresh active bin via discover_lb_pool.py before execution.",
    ),
    "sector_one_weth_usdt0": Preset(
        name="sector_one_weth_usdt0",
        chain="megaeth",
        chain_id=4326,
        dex_name="Sector One",
        router_address="0xd02bECF89D2670BAB93B738697Fa4D59B4f57B5E",
        token_x_symbol="WETH",
        token_x_address="0x4200000000000000000000000000000000000006",
        token_x_decimals=18,
        token_y_symbol="USDT0",
        token_y_address="0xb8ce59fc3717ada4c02eadf9682a9e934f625ebb",
        token_y_decimals=6,
        bin_step=10,
        default_active_bin_id=None,
        pool_address="0x341dc63fFCcF561214405c13c22abc81EFFBdf99",
        notes="Pool address is repo-backed, but active bin must still be refreshed live before execution.",
    ),
}


@dataclass
class CalldataPlan:
    preset: str
    chain: str
    chain_id: int
    dex_name: str
    router_address: str
    pool_address: str | None
    token_x_symbol: str
    token_x_address: str
    token_y_symbol: str
    token_y_address: str
    bin_step: int
    active_bin_id: int
    active_bin_source: str
    total_bins: int
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
    approvals_required: list[dict[str, Any]]
    calldata: str
    notes: str


def load_router_abi() -> list[dict[str, Any]]:
    return json.loads(ROUTER_ABI_PATH.read_text())


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
    if active_bin_id not in bin_ids:
        raise ValueError("active_bin_id must be included in the centered-bin layout")

    center_index = bin_ids.index(active_bin_id)
    bins_below = [b for b in bin_ids if b < active_bin_id]
    bins_above = [b for b in bin_ids if b > active_bin_id]
    delta_ids = [bin_id - active_bin_id for bin_id in bin_ids]
    distribution_x = [0] * num_bins
    distribution_y = [0] * num_bins

    center_share = total_supply // num_bins
    distribution_x[center_index] = center_share
    distribution_y[center_index] = center_share

    if bins_above:
        x_side_share = (total_supply - center_share) // len(bins_above)
        for i in range(center_index + 1, num_bins):
            distribution_x[i] = x_side_share
        used_x = center_share + (x_side_share * len(bins_above))
        distribution_x[-1] += total_supply - used_x

    if bins_below:
        y_side_share = (total_supply - center_share) // len(bins_below)
        for i in range(center_index):
            distribution_y[i] = y_side_share
        used_y = center_share + (y_side_share * len(bins_below))
        distribution_y[center_index - 1] += total_supply - used_y

    distribution_x[-1] += total_supply - sum(distribution_x)
    distribution_y[center_index] += total_supply - sum(distribution_y)

    return delta_ids, distribution_x, distribution_y


def build_liquidity_params(
    *,
    preset: Preset,
    sender: str,
    amount_x_human: float,
    amount_y_human: float,
    active_bin_id: int,
    total_bins: int,
    slippage_percent: float,
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    amount_x_raw = to_raw(amount_x_human, preset.token_x_decimals)
    amount_y_raw = to_raw(amount_y_human, preset.token_y_decimals)
    amount_x_min_raw = int(amount_x_raw * (1 - slippage_percent / 100))
    amount_y_min_raw = int(amount_y_raw * (1 - slippage_percent / 100))
    deadline = int(time.time()) + 300
    bin_ids = centered_bins(active_bin_id, total_bins)
    delta_ids, distribution_x, distribution_y = build_centered_distributions(bin_ids, active_bin_id)
    id_slippage = int(slippage_percent * 10)

    params_tuple = (
        Web3.to_checksum_address(preset.token_x_address),
        Web3.to_checksum_address(preset.token_y_address),
        preset.bin_step,
        amount_x_raw,
        amount_y_raw,
        amount_x_min_raw,
        amount_y_min_raw,
        active_bin_id,
        id_slippage,
        delta_ids,
        distribution_x,
        distribution_y,
        Web3.to_checksum_address(sender),
        Web3.to_checksum_address(sender),
        deadline,
    )

    return params_tuple, {
        "bin_ids": bin_ids,
        "amount_x_raw": amount_x_raw,
        "amount_y_raw": amount_y_raw,
        "amount_x_min_raw": amount_x_min_raw,
        "amount_y_min_raw": amount_y_min_raw,
        "delta_ids": delta_ids,
        "distribution_x": distribution_x,
        "distribution_y": distribution_y,
        "deadline": deadline,
    }


def build_calldata(
    *,
    preset: Preset,
    sender: str,
    amount_x_human: float,
    amount_y_human: float,
    active_bin_id: int,
    total_bins: int,
    slippage_percent: float,
    spend_native_for_x_side: bool,
) -> CalldataPlan:
    abi = load_router_abi()
    contract = Web3().eth.contract(address=Web3.to_checksum_address(preset.router_address), abi=abi)
    params_tuple, built = build_liquidity_params(
        preset=preset,
        sender=sender,
        amount_x_human=amount_x_human,
        amount_y_human=amount_y_human,
        active_bin_id=active_bin_id,
        total_bins=total_bins,
        slippage_percent=slippage_percent,
    )

    method = "addLiquidityNATIVE" if spend_native_for_x_side else "addLiquidity"
    fn = contract.get_function_by_name(method)(params_tuple)
    calldata = fn._encode_transaction_data()
    value_wei = built["amount_x_raw"] if spend_native_for_x_side else 0

    approvals_required: list[dict[str, Any]] = []
    if spend_native_for_x_side:
        if built["amount_y_raw"] > 0:
            approvals_required.append({
                "token": preset.token_y_symbol,
                "token_address": preset.token_y_address,
                "spender": preset.router_address,
                "amount_raw": built["amount_y_raw"],
            })
    else:
        if built["amount_x_raw"] > 0:
            approvals_required.append({
                "token": preset.token_x_symbol,
                "token_address": preset.token_x_address,
                "spender": preset.router_address,
                "amount_raw": built["amount_x_raw"],
            })
        if built["amount_y_raw"] > 0:
            approvals_required.append({
                "token": preset.token_y_symbol,
                "token_address": preset.token_y_address,
                "spender": preset.router_address,
                "amount_raw": built["amount_y_raw"],
            })

    return CalldataPlan(
        preset=preset.name,
        chain=preset.chain,
        chain_id=preset.chain_id,
        dex_name=preset.dex_name,
        router_address=preset.router_address,
        pool_address=preset.pool_address,
        token_x_symbol=preset.token_x_symbol,
        token_x_address=preset.token_x_address,
        token_y_symbol=preset.token_y_symbol,
        token_y_address=preset.token_y_address,
        bin_step=preset.bin_step,
        active_bin_id=active_bin_id,
        active_bin_source=(
            "historical_snapshot_refresh_required" if preset.default_active_bin_id is not None else "caller_supplied_refresh_required"
        ),
        total_bins=total_bins,
        amount_x_raw=built["amount_x_raw"],
        amount_y_raw=built["amount_y_raw"],
        amount_x_min_raw=built["amount_x_min_raw"],
        amount_y_min_raw=built["amount_y_min_raw"],
        delta_ids=built["delta_ids"],
        distribution_x=built["distribution_x"],
        distribution_y=built["distribution_y"],
        to=Web3.to_checksum_address(sender),
        refund_to=Web3.to_checksum_address(sender),
        deadline=built["deadline"],
        method=method,
        value_wei=value_wei,
        approvals_required=approvals_required,
        calldata=calldata,
        notes=preset.notes,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Liquidity Book addLiquidity calldata from a preset.")
    parser.add_argument("--preset", choices=sorted(PRESETS.keys()), default="base_sector_one_weth_usdc")
    parser.add_argument("--sender", required=True)
    parser.add_argument("--amount-x", type=float, required=True, help="Human amount for token_x")
    parser.add_argument("--amount-y", type=float, required=True, help="Human amount for token_y")
    parser.add_argument("--active-bin", type=int, help="Live active bin id. Required if preset has no default.")
    parser.add_argument("--total-bins", type=int, default=50)
    parser.add_argument("--slippage-percent", type=float, default=0.5)
    parser.add_argument("--spend-native-for-x-side", action="store_true")
    parser.add_argument(
        "--bankr-format",
        action="store_true",
        help="Emit Bankr-ready JSON with ordered calls[] for handoff to the bankr skill.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preset = PRESETS[args.preset]
    active_bin_id = args.active_bin if args.active_bin is not None else preset.default_active_bin_id
    if active_bin_id is None:
        raise SystemExit(
            f"Preset '{preset.name}' does not have a committed active-bin snapshot. Supply --active-bin from a live read first."
        )

    plan = build_calldata(
        preset=preset,
        sender=args.sender,
        amount_x_human=args.amount_x,
        amount_y_human=args.amount_y,
        active_bin_id=active_bin_id,
        total_bins=args.total_bins,
        slippage_percent=args.slippage_percent,
        spend_native_for_x_side=args.spend_native_for_x_side,
    )
    plan_dict = asdict(plan)
    if args.bankr_format:
        payload = wrap_bankr_payload(
            summary={
                "action": "deposit",
                "dex": plan.dex_name,
                "pair": f"{plan.token_x_symbol}/{plan.token_y_symbol}",
                "pool_address": plan.pool_address,
                "amount_x": args.amount_x,
                "amount_y": args.amount_y,
                "active_bin_id": plan.active_bin_id,
                "total_bins": plan.total_bins,
                "method": plan.method,
                "router_address": plan.router_address,
            },
            chain_id=plan.chain_id,
            chain=plan.chain,
            calls=calls_from_add_plan(plan_dict),
        )
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(plan_dict, indent=2))


if __name__ == "__main__":
    main()
