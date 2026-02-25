from apidev.core.rules.operation_id import build_operation_id


def test_build_operation_id_from_domain_path() -> None:
    assert build_operation_id("billing/create_invoice.yaml") == "billing_create_invoice"
