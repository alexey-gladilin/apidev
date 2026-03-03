from dataclasses import dataclass

_KNOWN_NAMESPACES = {"validation", "compatibility", "generation", "runtime", "config"}


def _to_kebab_case(value: str) -> str:
    return value.strip().replace("_", "-").replace(" ", "-").lower()


def _normalize_namespaced_code(code: str, default_namespace: str) -> str:
    raw = str(code).strip()
    if "." in raw:
        namespace, _, suffix = raw.partition(".")
        namespace_normalized = _to_kebab_case(namespace)
        if namespace_normalized in _KNOWN_NAMESPACES and suffix.strip():
            return f"{namespace_normalized}.{_to_kebab_case(suffix)}"
    return f"{default_namespace}.{_to_kebab_case(raw)}"


@dataclass(slots=True, frozen=True)
class ValidationDiagnostic:
    code: str
    severity: str
    message: str
    location: str
    rule: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "rule": self.rule,
        }

    def normalized_code(self) -> str:
        return _normalize_namespaced_code(self.code, default_namespace="validation")
