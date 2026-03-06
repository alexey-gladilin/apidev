from typer.models import OptionInfo

_DEFAULT_UNWRAP_DEPTH = 64


def unwrap_option_default(value: object, *, max_depth: int = _DEFAULT_UNWRAP_DEPTH) -> object:
    current = value
    for _ in range(max_depth):
        if isinstance(current, OptionInfo):
            current = current.default
            continue
        default = getattr(current, "default", None)
        if default is current:
            break
        if default is not None or hasattr(current, "default"):
            current = default
            continue
        break
    return current
