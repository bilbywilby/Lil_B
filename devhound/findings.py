from dataclasses import dataclass
from typing import Optional


@dataclass
class Finding:
    rule_id: str
    level: str  # "error" | "warning" | "note"
    message: str
    path: str
    line: Optional[int] = None
    column: Optional[int] = None
    fix: Optional[str] = None
    fingerprint: Optional[str] = None  # never derived from secret values
