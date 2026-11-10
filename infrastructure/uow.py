from .db import SessionLocal
from .sql_repos import SqlDebtRepo, SqlUserRepo


class SqlUnitOfWork:
    """
    Контракт: изменения коммитятся ТОЛЬКО явным .commit().
    При исключении — автоматический rollback.
    """

    def __init__(self) -> None:
        self._session = None
        self.users: SqlUserRepo
        self.debts: SqlDebtRepo

    def __enter__(self) -> "SqlUnitOfWork":
        self._session = SessionLocal()
        self.users = SqlUserRepo(self._session)
        self.debts = SqlDebtRepo(self._session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type:
                self._session.rollback()
        finally:
            self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()