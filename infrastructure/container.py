"""Composition root для инфраструктуры.
Presentation получает отсюда фабрику UoW, не зная про SqlUnitOfWork.
"""
from __future__ import annotations

from application.ports import UnitOfWork, UnitOfWorkFactory

from .uow import SqlUnitOfWork


def make_uow() -> UnitOfWork:
    return SqlUnitOfWork()


def get_uow_factory() -> UnitOfWorkFactory:
    return make_uow