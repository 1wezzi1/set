"""Мелкие переиспользуемые виджеты для GUI."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class LabeledEntry(tk.Frame):
    """Метка + поле ввода в одной строке."""

    def __init__(self, master, label: str, width: int = 30, **kwargs):
        super().__init__(master, **kwargs)
        tk.Label(self, text=label, width=20, anchor="w").pack(side="left")
        self.var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(side="left", fill="x", expand=True)

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self.var.set(value)

    def clear(self) -> None:
        self.var.set("")


class TableView(ttk.Frame):
    """Таблица (Treeview) с заголовками и скроллбаром."""

    def __init__(self, master, columns: list[tuple[str, str, int]], **kwargs):
        """
        columns: [(column_id, header_text, width), ...]
        """
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

    def add_row(self, values: tuple, iid: str | None = None) -> str:
        return self.tree.insert("", "end", values=values, iid=iid)

    def selected_iid(self) -> str | None:
        sel = self.tree.selection()
        return sel[0] if sel else None


def show_error(parent, message: str) -> None:
    from tkinter import messagebox
    messagebox.showerror("Ошибка", message, parent=parent)


def show_info(parent, message: str) -> None:
    from tkinter import messagebox
    messagebox.showinfo("Готово", message, parent=parent)