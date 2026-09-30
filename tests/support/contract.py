"""Validate HTTP responses against the approved contract (research R13, ADR-0016)."""

from functools import cache
from pathlib import Path
from typing import Any

import httpx
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "specs" / "001-fundacao-da-api" / "contracts" / "openapi.yaml"
)
CONTRACT_URI = "urn:cofre:contract"


class ContractViolation(AssertionError):
    """The response does not match the contract."""


@cache
def load_contract() -> dict[str, Any]:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


@cache
def _registry() -> Registry:
    resource = Resource.from_contents(load_contract(), default_specification=DRAFT202012)
    return Registry().with_resource(CONTRACT_URI, resource)


def _deref(node: dict[str, Any]) -> dict[str, Any]:
    while "$ref" in node:
        pointer = node["$ref"].removeprefix("#/").split("/")
        node = load_contract()
        for part in pointer:
            node = node[part]
    return node


def _rebase(schema: Any) -> Any:
    """Point local ``#/...`` references at the contract document."""
    if isinstance(schema, dict):
        return {
            key: (CONTRACT_URI + value if key == "$ref" and value.startswith("#") else _rebase(value))
            for key, value in schema.items()
        }
    if isinstance(schema, list):
        return [_rebase(item) for item in schema]
    return schema


def _response_spec(
    status: int, operation: tuple[str, str] | None, component: str | None
) -> dict[str, Any]:
    contract = load_contract()
    if component is not None:
        return contract["components"]["responses"][component]
    method, path = operation
    responses = contract["paths"][path][method.lower()]["responses"]
    if str(status) not in responses:
        raise ContractViolation(f"status {status} não declarado para {method.upper()} {path}")
    return _deref(responses[str(status)])


def assert_response_matches(
    response: httpx.Response,
    *,
    operation: tuple[str, str] | None = None,
    component: str | None = None,
) -> None:
    if (operation is None) == (component is None):
        raise ValueError("Informe exatamente um entre operation e component.")

    spec = _response_spec(response.status_code, operation, component)

    for name, header in spec.get("headers", {}).items():
        header = _deref(header)
        value = response.headers.get(name)
        if value is None:
            if header.get("required"):
                raise ContractViolation(f"cabeçalho obrigatório ausente: {name}")
            continue
        errors = list(Draft202012Validator(header.get("schema", {})).iter_errors(value))
        if errors:
            raise ContractViolation(f"cabeçalho {name} inválido: {errors[0].message}")

    content = spec.get("content", {}).get("application/json")
    if content is None:
        return
    validator = Draft202012Validator(_rebase(content["schema"]), registry=_registry())
    errors = sorted(validator.iter_errors(response.json()), key=lambda error: error.path)
    if errors:
        raise ContractViolation("; ".join(error.message for error in errors))
