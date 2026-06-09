from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
PAIR_ABI_PATH = ROOT / "references" / "lb-pair-minimal-abi.json"


@dataclass
class BinPosition:
    bin_id: int
    lp_amount: int


@dataclass
class PositionResult:
    pool_address: str
    wallet: str
    rpc_url: str
    bins_scanned: list[int]
    positions: list[BinPosition]
    total_bins_with_liquidity: int


def load_pair_abi() -> list[dict[str, Any]]:
    return json.loads(PAIR_ABI_PATH.read_text())


def centered_bins(active_bin_id: int, total_bins: int) -> list[int]:
    left = total_bins // 2
    right = total_bins - left - 1
    return list(range(active_bin_id - left, active_bin_id + right + 1))


def parse_csv_ints(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def read_balances(rpc_url: str, pool_address: str, wallet: str, bin_ids: list[int]) -> list[BinPosition]:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    contract = w3.eth.contract(address=Web3.to_checksum_address(pool_address), abi=load_pair_abi())
    wallet_checksum = Web3.to_checksum_address(wallet)
    accounts = [wallet_checksum] * len(bin_ids)
    balances = contract.get_function_by_name("balanceOfBatch")(accounts, bin_ids).call()
    positions: list[BinPosition] = []
    for bin_id, balance in zip(bin_ids, balances):
        amount = int(balance)
        if amount > 0:
            positions.append(BinPosition(bin_id=bin_id, lp_amount=amount))
    return positions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read SectorOne LB LP balances per bin for a wallet.")
    parser.add_argument("--pool-address", required=True)
    parser.add_argument("--wallet", required=True)
    parser.add_argument("--rpc-url", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bin-ids", help="Comma-separated bin ids to check")
    group.add_argument("--active-bin", type=int, help="Center bin for a scan range")
    parser.add_argument("--total-bins", type=int, default=50, help="Used with --active-bin")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.bin_ids:
        bin_ids = parse_csv_ints(args.bin_ids)
    else:
        bin_ids = centered_bins(args.active_bin, args.total_bins)

    positions = read_balances(args.rpc_url, args.pool_address, args.wallet, bin_ids)
    result = PositionResult(
        pool_address=Web3.to_checksum_address(args.pool_address),
        wallet=Web3.to_checksum_address(args.wallet),
        rpc_url=args.rpc_url,
        bins_scanned=bin_ids,
        positions=positions,
        total_bins_with_liquidity=len(positions),
    )
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
