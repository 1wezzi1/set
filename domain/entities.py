from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Money:
    """Value object — деньги в копейках (int), чтобы избежать float."""

    amount: int

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money cannot be negative")

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        return Money(self.amount - other.amount)

    @classmethod
    def from_rub(cls, rub: float | Decimal | str) -> "Money":
        value = Decimal(str(rub))
        if value < 0:
            raise ValueError("Amount must be non-negative")
        return cls(int((value * 100).to_integral_value()))

    def to_rub(self) -> Decimal:
        return Decimal(self.amount) / 100

    def __str__(self) -> str:
        return f"{self.to_rub():.2f} RUB"


@dataclass(frozen=True)
class User:
    id: UUID
    name: str

    @classmethod
    def create(cls, name: str) -> "User":
        if not name or not name.strip():
            raise ValueError("User name must not be empty")
        return cls(id=uuid4(), name=name.strip())


@dataclass(frozen=True)
class Debt:
    """Кто кому и сколько должен."""

    debtor_id: UUID
    creditor_id: UUID
    amount: Money

    def __post_init__(self) -> None:
        if self.debtor_id == self.creditor_id:
            raise ValueError("User cannot owe themselves")
        if self.amount.amount <= 0:
            raise ValueError("Debt amount must be > 0")