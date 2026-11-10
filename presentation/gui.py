"""GUI-оболочка Debt Tracker.

Presentation-слой: только ввод/вывод. Вся бизнес-логика — в use cases.
Единственная зависимость от инфраструктуры — фабрика UoW (передаётся снаружи).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from uuid import UUID

from application.ports import UnitOfWorkFactory
from application.use_cases import (
    AddDebtUseCase,
    CancelCyclesUseCase,
    CreateUserUseCase,
    GetBalancesUseCase,
    ListDebtsUseCase,
    ListUsersUseCase,
)
from domain.entities import User


def show_error(parent, message: str) -> None:
    from tkinter import messagebox
    messagebox.showerror("Ошибка", message, parent=parent)


class LabeledEntry(tk.Frame):
    def __init__(self, master, label: str, width: int = 30, **kwargs):
        super().__init__(master, **kwargs)
        tk.Label(self, text=label, width=20, anchor="w").pack(side="left")
        self.var = tk.StringVar()
        tk.Entry(self, textvariable=self.var, width=width).pack(
            side="left", fill="x", expand=True
        )

    def get(self) -> str:
        return self.var.get().strip()

    def clear(self) -> None:
        self.var.set("")


class TableView(ttk.Frame):
    def __init__(self, master, columns: list[tuple[str, str, int]], **kwargs):
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(
            self,
            columns=[c[0] for c in columns],
            show="headings",
            selectmode="browse",
        )
        for cid, header, width in columns:
            self.tree.heading(cid, text=header)
            self.tree.column(cid, width=width, anchor="w")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def clear(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def add_row(self, values: tuple) -> None:
        self.tree.insert("", "end", values=values)


class DebtTrackerApp(tk.Tk):
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        super().__init__()
        self.uow_factory = uow_factory

        self.title("Debt Tracker — управление долгами")
        self.geometry("1000x650")
        self.minsize(800, 500)

        self._users_cache: list[User] = []

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.users_tab = UsersTab(notebook, self)
        self.debts_tab = DebtsTab(notebook, self)
        self.balances_tab = BalancesTab(notebook, self)

        notebook.add(self.users_tab, text="👥 Пользователи")
        notebook.add(self.debts_tab, text="💸 Долги")
        notebook.add(self.balances_tab, text="📊 Балансы и циклы")

        self.refresh_all()

    def get_users(self) -> list[User]:
        self._users_cache = ListUsersUseCase(self.uow_factory).execute()
        return self._users_cache

    def refresh_all(self) -> None:
        self.get_users()
        self.users_tab.refresh()
        self.debts_tab.refresh()
        self.balances_tab.refresh()


class UsersTab(ttk.Frame):
    def __init__(self, master, app: DebtTrackerApp):
        super().__init__(master)
        self.app = app

        form = ttk.LabelFrame(self, text="Добавить пользователя", padding=8)
        form.pack(fill="x", padx=8, pady=8)

        self.name_entry = LabeledEntry(form, "Имя:")
        self.name_entry.pack(fill="x", pady=4)

        btn_frame = ttk.Frame(form)
        btn_frame.pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Добавить", command=self.on_add).pack(side="left")
        ttk.Button(btn_frame, text="Обновить список", command=self.refresh).pack(
            side="left", padx=6
        )

        list_frame = ttk.LabelFrame(self, text="Все пользователи", padding=8)
        list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.table = TableView(
            list_frame,
            columns=[("id", "ID", 300), ("name", "Имя", 200)],
        )
        self.table.pack(fill="both", expand=True)

    def refresh(self) -> None:
        self.table.clear()
        for user in self.app.get_users():
            self.table.add_row((str(user.id), user.name))

    def on_add(self) -> None:
        name = self.name_entry.get()
        if not name:
            show_error(self, "Имя не может быть пустым")
            return
        try:
            CreateUserUseCase(self.app.uow_factory).execute(name)
        except ValueError as e:
            show_error(self, str(e))
            return
        self.name_entry.clear()
        self.app.refresh_all()


class DebtsTab(ttk.Frame):
    def __init__(self, master, app: DebtTrackerApp):
        super().__init__(master)
        self.app = app

        form = ttk.LabelFrame(self, text="Добавить долг", padding=8)
        form.pack(fill="x", padx=8, pady=8)

        row1 = ttk.Frame(form)
        row1.pack(fill="x", pady=4)
        ttk.Label(row1, text="Должник:", width=12).pack(side="left")
        self.debtor_cb = ttk.Combobox(row1, state="readonly")
        self.debtor_cb.pack(side="left", fill="x", expand=True, padx=4)

        row2 = ttk.Frame(form)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Кредитор:", width=12).pack(side="left")
        self.creditor_cb = ttk.Combobox(row2, state="readonly")
        self.creditor_cb.pack(side="left", fill="x", expand=True, padx=4)

        row3 = ttk.Frame(form)
        row3.pack(fill="x", pady=4)
        ttk.Label(row3, text="Сумма (₽):", width=12).pack(side="left")
        self.amount_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.amount_var).pack(
            side="left", fill="x", expand=True, padx=4
        )

        btn_frame = ttk.Frame(form)
        btn_frame.pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="Добавить долг", command=self.on_add).pack(side="left")
        ttk.Button(btn_frame, text="Обновить", command=self.refresh).pack(
            side="left", padx=6
        )

        list_frame = ttk.LabelFrame(self, text="Все долги", padding=8)
        list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.table = TableView(
            list_frame,
            columns=[
                ("debtor", "Должник", 200),
                ("creditor", "Кредитор", 200),
                ("amount", "Сумма", 150),
            ],
        )
        self.table.pack(fill="both", expand=True)

    def refresh(self) -> None:
        users = self.app.get_users()
        names = [f"{u.name} ({str(u.id)[:8]})" for u in users]
        self.debtor_cb["values"] = names
        self.creditor_cb["values"] = names

        debts = ListDebtsUseCase(self.app.uow_factory).execute()
        users_map = {usr.id: usr.name for usr in users}

        self.table.clear()
        for d in debts:
            self.table.add_row(
                (
                    users_map.get(d.debtor_id, str(d.debtor_id)),
                    users_map.get(d.creditor_id, str(d.creditor_id)),
                    str(d.amount),
                )
            )

    def _parse_combobox_user(self, cb: ttk.Combobox) -> UUID | None:
        idx = cb.current()
        if idx < 0:
            return None
        users = self.app.get_users()
        if idx >= len(users):
            return None
        return users[idx].id

    def on_add(self) -> None:
        debtor_id = self._parse_combobox_user(self.debtor_cb)
        creditor_id = self._parse_combobox_user(self.creditor_cb)
        if debtor_id is None or creditor_id is None:
            show_error(self, "Выберите должника и кредитора")
            return
        if debtor_id == creditor_id:
            show_error(self, "Должник и кредитор не могут совпадать")
            return

        try:
            amount = float(self.amount_var.get().replace(",", "."))
        except ValueError:
            show_error(self, "Сумма должна быть числом")
            return
        if amount <= 0:
            show_error(self, "Сумма должна быть > 0")
            return

        try:
            AddDebtUseCase(self.app.uow_factory).execute(
                debtor_id, creditor_id, amount
            )
        except ValueError as e:
            show_error(self, str(e))
            return

        self.amount_var.set("")
        self.app.refresh_all()


class BalancesTab(ttk.Frame):
    def __init__(self, master, app: DebtTrackerApp):
        super().__init__(master)
        self.app = app

        action = ttk.LabelFrame(self, text="Взаимозачёт", padding=8)
        action.pack(fill="x", padx=8, pady=8)

        ttk.Button(
            action, text="🔁 Отменить все циклы", command=self.on_cancel_cycles
        ).pack(side="left")
        ttk.Button(action, text="🔄 Обновить", command=self.refresh).pack(
            side="left", padx=6
        )

        bal_frame = ttk.LabelFrame(
            self, text="Реальные долги (после нетто-расчёта)", padding=8
        )
        bal_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.balance_table = TableView(
            bal_frame,
            columns=[
                ("from", "Кто должен", 200),
                ("to", "Кому", 200),
                ("amount", "Сумма", 150),
            ],
        )
        self.balance_table.pack(fill="both", expand=True)

        log_frame = ttk.LabelFrame(self, text="Лог отмены циклов", padding=8)
        log_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.log_text = tk.Text(log_frame, height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True)

    def refresh(self) -> None:
        self.balance_table.clear()
        try:
            balances = GetBalancesUseCase(self.app.uow_factory).execute()
        except Exception as e:  # noqa: BLE001
            show_error(self, str(e))
            return
        if not balances:
            self.balance_table.add_row(("—", "—", "долгов нет"))
        else:
            for b in balances:
                self.balance_table.add_row((b["from"], b["to"], b["amount"]))

    def on_cancel_cycles(self) -> None:
        try:
            result = CancelCyclesUseCase(self.app.uow_factory).execute()
        except Exception as e:  # noqa: BLE001
            show_error(self, str(e))
            return

        self.log_text.delete("1.0", "end")
        if not result["cancelled_cycles"]:
            self.log_text.insert("end", "Циклов не найдено.\n")
        else:
            self.log_text.insert(
                "end", f"Отменено циклов: {len(result['cancelled_cycles'])}\n\n"
            )
            users_map = {
                str(u.id): u.name
                for u in ListUsersUseCase(self.app.uow_factory).execute()
            }
            for c in result["cancelled_cycles"]:
                names = " → ".join(users_map.get(uid, uid[:8]) for uid in c["cycle"])
                first = names.split(" → ")[0]
                self.log_text.insert(
                    "end",
                    f"  [{names} → {first}] = {c['amount_rub']:.2f} ₽\n",
                )
            self.log_text.insert(
                "end", f"\nОсталось долгов: {result['remaining_debts']}\n"
            )

        self.app.refresh_all()


def run(uow_factory: UnitOfWorkFactory) -> None:
    app = DebtTrackerApp(uow_factory)
    app.mainloop()