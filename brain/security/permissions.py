from enum import Enum


class PermissionLevel(str, Enum):
    READ = "read"
    LOW_RISK_WRITE = "low_risk_write"
    HIGH_RISK = "high_risk"
    DANGEROUS = "dangerous"


def requires_confirmation(level: PermissionLevel) -> bool:
    return level in (PermissionLevel.HIGH_RISK, PermissionLevel.DANGEROUS)
