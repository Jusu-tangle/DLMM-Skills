from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import requests
from web3 import Web3


ROOT = Path(__file__).resolve().parents[1]
PAIR_ABI_PATH = ROOT / "references" / "lb-pair-minimal-abi.json"


API_DEFAULTS: dict[str, dict[str, Any]] = {
    "sector_one_base": {
        "base_url": "https://api.sectorone.xyz",
        "chain_id": 8453,
        "chain": "base",
        "dex_name": "Sector One",
    },
    "sector_one": {
        "base_url": "https://api.sectorone.xyz",
        "chain_id": 4326,
        "chain": "megaeth",
        "dex_name": "Sector One",
    },
}

def resolve_snapshot_path(source: str) -> Path | None:
    candidates = [
        ROOT / "data" / f"{source}_pools.json",
        ROOT / "data" / "swapline_dump.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


@dataclass
class PoolDiscoveryResult:
    source: str
    chain: str
    chain_id: int
    dex_name: str
    base_url: str
    pool_address: str
    pool_name: str
    bin_step: int
    base_fee_pct: float | None
    lb_version: str | None
    token_x_symbol: str
    token_x_address: str
    token_x_decimals: int | None
    token_y_symbol: str
    token_y_address: str
    token_y_decimals: int | None
    liquidity_usd: float | None
    volume_24h_usd: float | None
    active_bin_id: int | None
    active_bin_source: str | None
    pool_data_source: str


def load_pair_abi() -> list[dict[str, Any]]:
    return json.loads(PAIR_ABI_PATH.read_text())


def load_local_snapshot(source: str) -> list[dict[str, Any]]:
    snapshot_path = resolve_snapshot_path(source)
    if snapshot_path is None:
        raise FileNotFoundError(
            f"No local snapshot for source '{source}'. Place JSON at data/{source}_pools.json or ensure api.sectorone.xyz is reachable."
        )
    data = json.loads(snapshot_path.read_text())
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return data["data"]
    raise ValueError(f"Unsupported snapshot format for source '{source}'")


def fetch_pools(source: str, base_url: str) -> tuple[list[dict[str, Any]], str]:
    try:
        response = requests.get(f"{base_url}/api/v1/pools", timeout=10)
        response.raise_for_status()
        data = response.json()
        pools = data if isinstance(data, list) else []
        return pools, "live_api"
    except requests.RequestException:
        pools = load_local_snapshot(source)
        snapshot_path = resolve_snapshot_path(source)
        label = snapshot_path.name if snapshot_path else "missing"
        return pools, f"local_snapshot:{label}"


def checksum_or_original(address: str | None) -> str | None:
    if not address:
        return address
    if address.startswith("0x") and len(address) == 42:
        try:
            return Web3.to_checksum_address(address)
        except Exception:
            return address
    return address


def match_pool(
    pools: list[dict[str, Any]],
    *,
    pool_address: str | None,
    token_x: str | None,
    token_y: str | None,
    bin_step: int | None,
    chain_id: int | None = None,
) -> dict[str, Any]:
    if chain_id is not None:
        pools = [pool for pool in pools if int(pool.get("chainId", 0) or 0) == chain_id]

    if pool_address:
        target = pool_address.lower()
        for pool in pools:
            if str(pool.get("address", "")).lower() == target:
                return pool
        raise ValueError(f"Pool address not found: {pool_address}")

    if not token_x or not token_y:
        raise ValueError("token_x and token_y are required when pool_address is not provided")

    token_x_upper = token_x.upper()
    token_y_upper = token_y.upper()
    matches: list[dict[str, Any]] = []
    for pool in pools:
        pool_x = str((pool.get("tokenX") or {}).get("symbol", "")).upper()
        pool_y = str((pool.get("tokenY") or {}).get("symbol", "")).upper()
        if pool_x == token_x_upper and pool_y == token_y_upper:
            matches.append(pool)
        elif pool_x == token_y_upper and pool_y == token_x_upper:
            matches.append(pool)

    if not matches:
        raise ValueError(f"No pool found for {token_x}-{token_y}")

    if bin_step is not None:
        filtered = [pool for pool in matches if int(pool.get("binStep", 0) or 0) == bin_step]
        if filtered:
            matches = filtered

    matches.sort(key=lambda pool: float(pool.get("liquidityUSD", 0.0) or 0.0), reverse=True)
    return matches[0]


def try_read_active_bin(rpc_url: str | None, pool_address: str) -> tuple[int | None, str | None]:
    if not rpc_url:
        return None, None
    abi = load_pair_abi()
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    contract = w3.eth.contract(address=Web3.to_checksum_address(pool_address), abi=abi)
    active_id = contract.get_function_by_name("getActiveId")().call()
    return int(active_id), "rpc:getActiveId"


def build_result(source: str, base_url: str, pool: dict[str, Any], rpc_url: str | None, pool_data_source: str) -> PoolDiscoveryResult:
    defaults = API_DEFAULTS[source]
    pool_address = checksum_or_original(str(pool.get("address", ""))) or ""
    active_bin_id, active_source = try_read_active_bin(rpc_url, pool_address)
    token_x = pool.get("tokenX") or {}
    token_y = pool.get("tokenY") or {}
    return PoolDiscoveryResult(
        source=source,
        chain=str(defaults["chain"]),
        chain_id=int(pool.get("chainId") or defaults["chain_id"]),
        dex_name=str(defaults["dex_name"]),
        base_url=base_url,
        pool_address=pool_address,
        pool_name=str(pool.get("name", "")),
        bin_step=int(pool.get("binStep", 0) or 0),
        base_fee_pct=float(pool.get("baseFeePct")) if pool.get("baseFeePct") is not None else None,
        lb_version=str(pool.get("lbVersion")) if pool.get("lbVersion") is not None else None,
        token_x_symbol=str(token_x.get("symbol", "")),
        token_x_address=checksum_or_original(token_x.get("address")) or "",
        token_x_decimals=int(token_x.get("decimals")) if token_x.get("decimals") is not None else None,
        token_y_symbol=str(token_y.get("symbol", "")),
        token_y_address=checksum_or_original(token_y.get("address")) or "",
        token_y_decimals=int(token_y.get("decimals")) if token_y.get("decimals") is not None else None,
        liquidity_usd=float(pool.get("liquidityUSD")) if pool.get("liquidityUSD") is not None else None,
        volume_24h_usd=float(pool.get("volumeUSD")) if pool.get("volumeUSD") is not None else None,
        active_bin_id=active_bin_id,
        active_bin_source=active_source,
        pool_data_source=pool_data_source,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover a Liquidity Book pool from a live API and optionally read the active bin from RPC.")
    parser.add_argument("--source", choices=sorted(API_DEFAULTS.keys()), required=True)
    parser.add_argument("--pool-address")
    parser.add_argument("--token-x")
    parser.add_argument("--token-y")
    parser.add_argument("--bin-step", type=int)
    parser.add_argument("--base-url", help="Override the default API base URL")
    parser.add_argument("--rpc-url", help="Optional RPC URL for getActiveId()")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    defaults = API_DEFAULTS[args.source]
    base_url = args.base_url or str(defaults["base_url"])
    pools, pool_data_source = fetch_pools(args.source, base_url)
    pool = match_pool(
        pools,
        pool_address=args.pool_address,
        token_x=args.token_x,
        token_y=args.token_y,
        bin_step=args.bin_step,
        chain_id=int(defaults["chain_id"]),
    )
    result = build_result(args.source, base_url, pool, args.rpc_url, pool_data_source)
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
