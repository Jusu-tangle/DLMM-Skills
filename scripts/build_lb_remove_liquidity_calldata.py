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
from bankr_calls import calls_from_remove_plan, wrap_bankr_payload


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
    token_y_symbol: str
    token_y_address: str
    bin_step: int
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
        token_y_symbol="USDC",
        token_y_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        bin_step=4,
        pool_address="0xf69bc3e0fdaa8016094468bfb7ef77b4c4f33b4b",
        notes="LB v2.0 router. setApprovalForAll(router,true) on the LB pair may be required before router withdrawal.",
    ),
    "sector_one_weth_usdt0": Preset(
        name="sector_one_weth_usdt0",
        chain="megaeth",
        chain_id=4326,
        dex_name="Sector One",
        router_address="0xd02bECF89D2670BAB93B738697Fa4D59B4f57B5E",
        token_x_symbol="WETH",
        token_x_address="0x4200000000000000000000000000000000000006",
        token_y_symbol="USDT0",
        token_y_address="0xb8ce59fc3717ada4c02eadf9682a9e934f625ebb",
        bin_step=10,
        pool_address="0x341dc63fFCcF561214405c13c22abc81EFFBdf99",
        notes="Sector One remove-liquidity example. Pool address is repo-backed, but active state and LP balances still need to be refreshed live.",
    ),
}


@dataclass
class RemoveCalldataPlan:
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
    ids: list[int]
    amounts: list[int]
    amount_x_min_raw: int
    amount_y_min_raw: int
    amount_token_min_raw: int | None
    amount_native_min_raw: int | None
    to: str
    deadline: int
    method: str
    operator_approval_required: bool
    operator_approval_target: str
    calldata: str
    notes: str


def load_router_abi() -> list[dict[str, Any]]:
    return json.loads(ROUTER_ABI_PATH.read_text())


def parse_csv_ints(raw: str) -> list[int]:
    values = [part.strip() for part in raw.split(",") if part.strip()]
    return [int(value) for value in values]


def scale_amounts(amounts: list[int], withdraw_percent: float) -> list[int]:
    if not 0 < withdraw_percent <= 100:
        raise ValueError("withdraw_percent must be between 0 and 100")
    factor = withdraw_percent / 100.0
    scaled: list[int] = []
    for amount in amounts:
        value = int(amount * factor)
        if amount > 0 and value == 0:
            value = 1
        scaled.append(value)
    return scaled


def filter_zero_bins(ids: list[int], amounts: list[int]) -> tuple[list[int], list[int]]:
    filtered_ids: list[int] = []
    filtered_amounts: list[int] = []
    for bin_id, amount in zip(ids, amounts):
        if amount <= 0:
            continue
        filtered_ids.append(bin_id)
        filtered_amounts.append(amount)
    return filtered_ids, filtered_amounts


def build_calldata(
    *,
    preset: Preset,
    sender: str,
    ids: list[int],
    amounts: list[int],
    withdraw_percent: float,
    amount_x_min_raw: int,
    amount_y_min_raw: int,
    claim_native_for_x_side: bool,
) -> RemoveCalldataPlan:
    if len(ids) != len(amounts):
        raise ValueError("ids and amounts must have the same length")

    scaled_amounts = scale_amounts(amounts, withdraw_percent)
    filtered_ids, filtered_amounts = filter_zero_bins(ids, scaled_amounts)
    if not filtered_ids:
        raise ValueError("No positive LP amounts remain after scaling/filtering")

    abi = load_router_abi()
    contract = Web3().eth.contract(address=Web3.to_checksum_address(preset.router_address), abi=abi)
    deadline = int(time.time()) + 300
    sender_checksum = Web3.to_checksum_address(sender)

    if claim_native_for_x_side:
        method = "removeLiquidityNATIVE"
        params = (
            Web3.to_checksum_address(preset.token_y_address),
            preset.bin_step,
            int(amount_y_min_raw),
            int(amount_x_min_raw),
            filtered_ids,
            filtered_amounts,
            sender_checksum,
            deadline,
        )
        amount_token_min_raw = int(amount_y_min_raw)
        amount_native_min_raw = int(amount_x_min_raw)
    else:
        method = "removeLiquidity"
        params = (
            Web3.to_checksum_address(preset.token_x_address),
            Web3.to_checksum_address(preset.token_y_address),
            preset.bin_step,
            int(amount_x_min_raw),
            int(amount_y_min_raw),
            filtered_ids,
            filtered_amounts,
            sender_checksum,
            deadline,
        )
        amount_token_min_raw = None
        amount_native_min_raw = None

    fn = contract.get_function_by_name(method)(*params)
    calldata = fn._encode_transaction_data()

    return RemoveCalldataPlan(
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
        ids=filtered_ids,
        amounts=filtered_amounts,
        amount_x_min_raw=int(amount_x_min_raw),
        amount_y_min_raw=int(amount_y_min_raw),
        amount_token_min_raw=amount_token_min_raw,
        amount_native_min_raw=amount_native_min_raw,
        to=sender_checksum,
        deadline=deadline,
        method=method,
        operator_approval_required=True,
        operator_approval_target=preset.router_address,
        calldata=calldata,
        notes=preset.notes,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Liquidity Book removeLiquidity calldata from a preset.")
    parser.add_argument("--preset", choices=sorted(PRESETS.keys()), default="base_sector_one_weth_usdc")
    parser.add_argument("--sender", required=True)
    parser.add_argument("--ids", required=True, help="Comma-separated bin ids")
    parser.add_argument("--amounts", required=True, help="Comma-separated LP token amounts matching ids")
    parser.add_argument("--withdraw-percent", type=float, default=100.0)
    parser.add_argument("--amount-x-min-raw", type=int, default=0)
    parser.add_argument("--amount-y-min-raw", type=int, default=0)
    parser.add_argument("--claim-native-for-x-side", action="store_true")
    parser.add_argument(
        "--bankr-format",
        action="store_true",
        help="Emit Bankr-ready JSON with ordered calls[] for handoff to the bankr skill.",
    )
    parser.add_argument(
        "--skip-operator-approval",
        action="store_true",
        help="Omit approveForAll on the LB pair (only if already approved).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preset = PRESETS[args.preset]
    ids = parse_csv_ints(args.ids)
    amounts = parse_csv_ints(args.amounts)
    plan = build_calldata(
        preset=preset,
        sender=args.sender,
        ids=ids,
        amounts=amounts,
        withdraw_percent=args.withdraw_percent,
        amount_x_min_raw=args.amount_x_min_raw,
        amount_y_min_raw=args.amount_y_min_raw,
        claim_native_for_x_side=args.claim_native_for_x_side,
    )
    plan_dict = asdict(plan)
    if args.bankr_format:
        payload = wrap_bankr_payload(
            summary={
                "action": "withdraw",
                "dex": plan.dex_name,
                "pair": f"{plan.token_x_symbol}/{plan.token_y_symbol}",
                "pool_address": plan.pool_address,
                "bin_ids": plan.ids,
                "lp_amounts": plan.amounts,
                "withdraw_percent": args.withdraw_percent,
                "method": plan.method,
                "router_address": plan.router_address,
            },
            chain_id=plan.chain_id,
            chain=plan.chain,
            calls=calls_from_remove_plan(
                plan_dict,
                include_operator_approval=not args.skip_operator_approval,
            ),
        )
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(plan_dict, indent=2))


if __name__ == "__main__":
    main()
