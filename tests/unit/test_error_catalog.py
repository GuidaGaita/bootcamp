import pytest

from cofre.api.errors import CATALOG, validation_details
from tests.support.contract import load_contract

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-14", "RNF-04")]


def _error(loc, error_type, value="MARCADOR-INPUT") -> dict:
    return {"type": error_type, "loc": loc, "msg": f"bad {value}", "input": value}


def test_catalog_codes_belong_to_contract_enum():
    enum = set(load_contract()["components"]["schemas"]["ErrorCode"]["enum"])

    assert set(CATALOG) <= enum
    for status, message in CATALOG.values():
        assert 400 <= status < 600
        assert message.strip()


def test_json_invalid_maps_to_body():
    details = validation_details([_error(("body", 12), "json_invalid")])

    assert [d.model_dump() for d in details] == [{"field": "body", "issue": "JSON malformado."}]


def test_missing_body_field_strips_location_prefix():
    details = validation_details([_error(("body", "name"), "missing")])

    assert [d.model_dump() for d in details] == [{"field": "name", "issue": "Campo obrigatório."}]


def test_query_parsing_error_maps_to_type_issue():
    details = validation_details([_error(("query", "limit"), "int_parsing")])

    assert [d.model_dump() for d in details] == [
        {"field": "limit", "issue": "Tipo de valor inválido."}
    ]


def test_type_error_maps_to_type_issue():
    details = validation_details([_error(("body", "name"), "string_type")])

    assert details[0].issue == "Tipo de valor inválido."


def test_nested_location_is_joined_with_dots():
    details = validation_details([_error(("body", "items", 0, "url"), "missing")])

    assert details[0].field == "items.0.url"


def test_location_without_remaining_segment_maps_to_body():
    details = validation_details([_error(("body",), "missing")])

    assert details[0].field == "body"


def test_unknown_error_type_maps_to_generic_issue():
    details = validation_details([_error(("body", "name"), "something_new")])

    assert details[0].issue == "Valor inválido."


def test_received_input_never_appears_in_details():
    errors = [
        _error(("body", "name"), kind)
        for kind in ("missing", "json_invalid", "string_type", "int_parsing", "value_error")
    ]

    rendered = str([d.model_dump() for d in validation_details(errors)])

    assert "MARCADOR-INPUT" not in rendered
