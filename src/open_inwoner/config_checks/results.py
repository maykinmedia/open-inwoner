from dataclasses import dataclass, field


@dataclass
class CheckResult:
    success: bool
    identifier: str
    verbose_name: str
    message: str
    extra: dict = field(default_factory=dict)
