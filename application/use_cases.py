from uuid import UUID

from domain.entities import Debt, Money, User
from domain.graph import CycleCanceller, DebtGraph, Edge
from domain.services import DebtSimplifier

from .ports import UnitOfWork, UnitOfWorkFactory


class CreateUserUseCase:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def execute(self, name: str) -> User:
        user = User.create(name)
        with self.uow_factory() as u:
            u.users.add(user)
            u.commit()
        return user


class ListUsersUseCase:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def execute(self) -> list[User]:
        with self.uow_factory() as u:
            return u.users.all()


class ListDebtsUseCase:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def execute(self) -> list[Debt]:
        with self.uow_factory() as u:
            return u.debts.all()


class AddDebtUseCase:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def execute(self, debtor_id: UUID, creditor_id: UUID, rub: float) -> Debt:
        with self.uow_factory() as u:
            if not u.users.get(debtor_id):
                raise ValueError("Debtor not found")
            if not u.users.get(creditor_id):
                raise ValueError("Creditor not found")
            debt = Debt(debtor_id, creditor_id, Money.from_rub(rub))
            u.debts.add(debt)
            u.commit()
        return debt


class CancelCyclesUseCase:
    """Находит все циклы и вычёркивает их. Атомарно."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def execute(self) -> dict:
        with self.uow_factory() as u:
            debts = u.debts.all()
            edges = [
                Edge(d.debtor_id, d.creditor_id, d.amount.amount) for d in debts
            ]
            graph = DebtGraph(edges)
            remaining_edges, cancellations = CycleCanceller.cancel_all(graph)

            new_debts = [
                Debt(e.debtor_id, e.creditor_id, Money(e.weight))
                for e in remaining_edges
            ]
            u.debts.replace_all(new_debts)
            u.commit()

            return {
                "cancelled_cycles": [
                    {
                        "cycle": [str(uid) for uid in c.cycle],
                        "amount_rub": float(Money(c.amount).to_rub()),
                    }
                    for c in cancellations
                ],
                "remaining_debts": len(new_debts),
            }


class GetBalancesUseCase:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def execute(self) -> list[dict]:
        with self.uow_factory() as u:
            debts = u.debts.all()
            users = {usr.id: usr.name for usr in u.users.all()}

        simplified = DebtSimplifier.simplify(debts)
        return [
            {
                "from": users[d.debtor_id],
                "to": users[d.creditor_id],
                "amount": str(d.amount),
            }
            for d in simplified
        ]