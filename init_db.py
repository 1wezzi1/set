"""Инициализация БД Debt Tracker.

Использование:
    python init_db.py              # создать БД + таблицы (если нет)
    python init_db.py --reset      # УДАЛИТЬ и создать заново
    python init_db.py --demo       # создать + заполнить демо-данными
"""
from __future__ import annotations

import argparse
import os
import sys

from infrastructure import models  # noqa: F401 — регистрирует модели
from infrastructure.db import Base, DATABASE_URL, engine
from infrastructure.container import get_uow_factory

from application.use_cases import (
    AddDebtUseCase,
    CancelCyclesUseCase,
    CreateUserUseCase,
    GetBalancesUseCase,
)


DB_PATH = DATABASE_URL.replace("sqlite:///", "")


def print_status() -> None:
    print(f"📁 Файл БД: {os.path.abspath(DB_PATH)}")
    exists = os.path.exists(DB_PATH)
    size = os.path.getsize(DB_PATH) if exists else 0
    print(f"   существует: {'да' if exists else 'нет'} ({size} байт)")
    print()


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы (или уже существовали)")


def reset_db() -> None:
    confirm = input(
        f"⚠️  Удалить ВСЕ данные из {DB_PATH}? Введите 'yes' для подтверждения: "
    )
    if confirm.strip().lower() != "yes":
        print("Отменено.")
        sys.exit(0)
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    print("🗑️  Старая БД удалена")
    Base.metadata.create_all(bind=engine)
    print("✅ Новая БД создана")


def seed_demo() -> None:
    factory = get_uow_factory()

    print("\n🌱 Заполняем демо-данными...")
    a = CreateUserUseCase(factory).execute("Алиса")
    b = CreateUserUseCase(factory).execute("Боб")
    c = CreateUserUseCase(factory).execute("Чарли")
    d = CreateUserUseCase(factory).execute("Дана")
    print(f"   созданы: {a.name}, {b.name}, {c.name}, {d.name}")

    add = AddDebtUseCase(factory)
    add.execute(a.id, b.id, 100)   # цикл
    add.execute(b.id, c.id, 100)   # цикл
    add.execute(c.id, a.id, 100)   # цикл
    add.execute(c.id, d.id, 50)    # не цикл
    print("   добавлено 4 долга (3 из них образуют цикл)")

    print("\n📊 Балансы ДО отмены циклов:")
    for row in GetBalancesUseCase(factory).execute():
        print(f"   {row['from']} → {row['to']}: {row['amount']}")

    print("\n🔁 Отменяем циклы...")
    result = CancelCyclesUseCase(factory).execute()
    for cyc in result["cancelled_cycles"]:
        print(f"   цикл на {cyc['amount_rub']:.2f} ₽")
    print(f"   осталось долгов: {result['remaining_debts']}")

    print("\n📊 Балансы ПОСЛЕ:")
    for row in GetBalancesUseCase(factory).execute():
        print(f"   {row['from']} → {row['to']}: {row['amount']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Инициализация БД Debt Tracker")
    parser.add_argument("--reset", action="store_true", help="удалить и создать заново")
    parser.add_argument("--demo", action="store_true", help="заполнить демо-данными")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║  Debt Tracker — инициализация БД        ║")
    print("╚══════════════════════════════════════════╝\n")
    print_status()

    if args.reset:
        reset_db()
    else:
        create_tables()

    if args.demo:
        seed_demo()

    print("\n✨ Готово. Запускайте:")
    print("   python run_gui.py         — GUI")
    print("   python main.py            — HTTP API")


if __name__ == "__main__":
    main()