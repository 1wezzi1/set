import uuid
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from domain.entities import Debt, Money, User

from .models import DebtModel, UserModel


class SqlUserRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, user: User) -> None:
        self.session.add(UserModel(id=user.id, name=user.name))

    def get(self, user_id: UUID) -> User | None:
        row = self.session.get(UserModel, user_id)
        return User(id=row.id, name=row.name) if row else None

    def all(self) -> list[User]:
        rows = self.session.scalars(select(UserModel)).all()
        return [User(id=r.id, name=r.name) for r in rows]


class SqlDebtRepo:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, debt: Debt) -> None:
        self.session.add(
            DebtModel(
                id=uuid.uuid4(),
                debtor_id=debt.debtor_id,
                creditor_id=debt.creditor_id,
                amount=debt.amount.amount,
            )
        )

    def all(self) -> list[Debt]:
        rows = self.session.scalars(select(DebtModel)).all()
        return [
            Debt(r.debtor_id, r.creditor_id, Money(r.amount)) for r in rows
        ]

    def replace_all(self, debts: list[Debt]) -> None:
        self.session.execute(delete(DebtModel))
        for d in debts:
            self.session.add(
                DebtModel(
                    id=uuid.uuid4(),
                    debtor_id=d.debtor_id,
                    creditor_id=d.creditor_id,
                    amount=d.amount.amount,
                )
            )