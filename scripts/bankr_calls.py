from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
ERC20_ABI_PATH = ROOT / "references" / "erc20-minimal-abi.json"
PAIR_ABI_PATH = ROOT / "references" / "lb-pair-minimal-abi.json"


def load_erc20_abi() -> list[dict[str, Any]]:
    return json.loads(ERC20_ABI_PATH.read_text())


def load_pair_abi() -> list[dict[str, Any]]:
    return json.loads(PAIR_ABI_PATH.read_text())


def checksum(address: str) -> str:
    return Web3.to_checksum_address(address)


def to_hex_value(wei: int) -> str:
    if wei <= 0:
        return "0x0"
    return hex(wei)


def encode_approve(token_address: str, spender: str, amount_raw: int) -> str:
    contract = Web3().eth.contract(address=checksum(token_address), abi=load_erc20_abi())
    return contract.get_function_by_name("approve")(checksum(spender), int(amount_raw))._encode_transaction_data()


def encode_approve_for_all(pair_address: str, operator: str, approved: bool = True) -> str:
    contract = Web3().eth.contract(address=checksum(pair_address), abi=load_pair_abi())
    return contract.get_function_by_name("approveForAll")(checksum(operator), approved)._encode_transaction_data()


def bankr_call(*, to: str, data: str, value_wei: int = 0, label: str) -> dict[str, str]:
    return {
        "to": checksum(to),
        "data": data,
        "value": to_hex_value(value_wei),
        "label": label,
    }


def calls_from_add_plan(plan: dict[str, Any]) -> list[dict[str, str]]:
    calls: list[dict[str, str]] = []
    for approval in plan.get("approvals_required", []):
        calls.append(
            bankr_call(
                to=str(approval["token_address"]),
                data=encode_approve(
                    str(approval["token_address"]),
                    str(approval["spender"]),
                    int(approval["amount_raw"]),
                ),
                label=f"approve {approval.get('token', 'token')}",
            )
        )
    calls.append(
        bankr_call(
            to=str(plan["router_address"]),
            data=str(plan["calldata"]),
            value_wei=int(plan.get("value_wei", 0)),
            label=str(plan.get("method", "addLiquidity")),
        )
    )
    return calls


def calls_from_remove_plan(plan: dict[str, Any], *, include_operator_approval: bool = True) -> list[dict[str, str]]:
    calls: list[dict[str, str]] = []
    if (
        include_operator_approval
        and plan.get("operator_approval_required")
        and plan.get("pool_address")
    ):
        calls.append(
            bankr_call(
                to=str(plan["pool_address"]),
                data=encode_approve_for_all(
                    str(plan["pool_address"]),
                    str(plan["operator_approval_target"]),
                ),
                label="approveForAll router on LB pair",
            )
        )
    calls.append(
        bankr_call(
            to=str(plan["router_address"]),
            data=str(plan["calldata"]),
            label=str(plan.get("method", "removeLiquidity")),
        )
    )
    return calls


def wrap_bankr_payload(
    *,
    summary: dict[str, Any],
    chain_id: int,
    chain: str,
    calls: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "summary": summary,
        "chainId": chain_id,
        "chain": chain,
        "calls": calls,
        "bankr_handoff": {
            "skill": "bankr",
            "action": "Submit each item in calls[] in order using the bankr skill (bankr wallet submit).",
            "rules": [
                "Show summary to the user and get explicit confirmation before any submit.",
                "Submit calls sequentially; wait for confirmation between steps.",
                "Stop on the first failed submit.",
                "Do not embed API keys in SectorOne skills — Bankr runtime provides auth.",
            ],
        },
    }
