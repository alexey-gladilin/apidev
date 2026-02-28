from apidev.application.services.diff_service import DiffService


def _serializer() -> DiffService:
    # Constructor dependencies are not needed for pure literal serialization checks.
    return object.__new__(DiffService)


def test_stable_python_literal_happy_path_nested_and_sorted_keys() -> None:
    service = _serializer()
    value = {"b": 2, "a": {"d": "x", "c": 1}}

    rendered = service._python_literal(value)

    assert rendered == '{"a": {"c": 1, "d": "x"}, "b": 2}'


def test_stable_python_literal_handles_none_bool_and_empty_values() -> None:
    service = _serializer()
    value = {"empty_dict": {}, "empty_list": [], "flag": True, "missing": None}

    rendered = service._python_literal(value)

    assert rendered == '{"empty_dict": {}, "empty_list": [], "flag": True, "missing": None}'


def test_stable_python_literal_boundary_values_unicode_and_single_tuple() -> None:
    service = _serializer()
    value = {"emoji": "ok: \u2713", "single": ("x",), "zero": 0}

    rendered = service._python_literal(value)

    assert rendered == '{"emoji": "ok: \u2713", "single": ("x",), "zero": 0}'


def test_stable_python_literal_falls_back_to_repr_for_unknown_objects() -> None:
    service = _serializer()

    class Unknown:
        def __repr__(self) -> str:
            return "Unknown()"

    rendered = service._python_literal({"x": Unknown()})

    assert rendered == '{"x": Unknown()}'


def test_stable_python_literal_deep_nesting_does_not_stack_overflow() -> None:
    """Deeply nested structures must not cause stack overflow; depth guard truncates."""
    service = _serializer()
    nested: dict = {"x": 1}
    for _ in range(200):
        nested = {"inner": nested}

    rendered = service._python_literal(nested)

    assert '"<truncated>"' in rendered
