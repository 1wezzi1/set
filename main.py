"""Точка входа HTTP API.

Запуск:
    python main.py
Swagger:
    http://localhost:8000/docs
"""
from infrastructure import models  # noqa: F401 — регистрирует ORM-модели
from infrastructure.db import Base, engine
from presentation.api import app

# Создаём таблицы (для продакшена — Alembic)
Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)