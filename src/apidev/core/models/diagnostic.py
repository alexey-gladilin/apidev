from dataclasses import dataclass


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
