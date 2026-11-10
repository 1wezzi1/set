from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from .entities import Debt, Money


class DebtSimplifier:
    """Нетто-балансы и минимальный набор транзакций. Чистый домен."""

    @staticmethod
    def net_balances(debts: list[Debt]) -> dict[UUID, int]:
        balances: dict[UUID, int] = defaultdict(int)
        for d in debts:
            balances[d.creditor_id] += d.amount.amount
            balances[d.debtor_id] -= d.amount.amount
        return dict(balances)

    @staticmethod
    def simplify(debts: list[Debt]) -> list[Debt]:
        balances = DebtSimplifier.net_balances(debts)

        creditors = [[uid, amt] for uid, amt in balances.items() if amt > 0]
        debtors = [[uid, -amt] for uid, amt in balances.items() if amt < 0]

        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

        result: list[Debt] = []
        i = j = 0
        while i < len(debtors) and j < len(creditors):
            debtor_id, debt_amt = debtors[i]
            creditor_id, cred_amt = creditors[j]
            pay = min(debt_amt, cred_amt)
            if pay > 0:
                result.append(Debt(debtor_id, creditor_id, Money(pay)))
            debtors[i][1] -= pay
            creditors[j][1] -= pay
            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1
        return result