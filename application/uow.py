from .db import SessionLocal
from .sql_repos import SqlUserRepo, SqlDebtRepo


class SqlUnitOfWork:
    """
    Контракт: изменения коммитятся ТОЛЬКО явным вызовом .commit().
    При выходе из контекста с исключением — автоматический rollback.
    Без исключения — rollback неявный (session.close()), данные теряются.
    """

    def __init__(self):
        self._session = None

    def __enter__(self):
        self._session = SessionLocal()
        self.users = SqlUserRepo(self._session)
        self.debts = SqlDebtRepo(self._session)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self._session.rollback()
        finally:
            self._session.close()

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()