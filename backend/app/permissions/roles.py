from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"

    @classmethod
    def from_value(cls, value: str | "Role") -> "Role":
        if isinstance(value, cls):
            return value

        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Unsupported role: {value}") from exc
