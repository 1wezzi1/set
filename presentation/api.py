import os
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from application.ports import UnitOfWorkFactory
from application.use_cases import (
    AddDebtUseCase,
    CancelCyclesUseCase,
    CreateUserUseCase,
    GetBalancesUseCase,
    ListDebtsUseCase,
    ListUsersUseCase,
)
from infrastructure.container import get_uow_factory

app = FastAPI(title="Debt Tracker Web")
router = APIRouter()


def _factory() -> UnitOfWorkFactory:
    return get_uow_factory()


class CreateUserReq(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class AddDebtReq(BaseModel):
    debtor_id: UUID
    creditor_id: UUID
    amount_rub: float = Field(gt=0)


# --- API Эндпоинты ---

@router.post("/users")
def create_user(req: CreateUserReq, factory: UnitOfWorkFactory = Depends(_factory)):
    try:
        u = CreateUserUseCase(factory).execute(req.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": str(u.id), "name": u.name}


@router.get("/users")
def list_users(factory: UnitOfWorkFactory = Depends(_factory)):
    users = ListUsersUseCase(factory).execute()
    return [{"id": str(u.id), "name": u.name} for u in users]


@router.post("/debts")
def add_debt(req: AddDebtReq, factory: UnitOfWorkFactory = Depends(_factory)):
    try:
        d = AddDebtUseCase(factory).execute(req.debtor_id, req.creditor_id, req.amount_rub)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"from": str(d.debtor_id), "to": str(d.creditor_id), "amount": str(d.amount)}


@router.get("/debts")
def list_debts(factory: UnitOfWorkFactory = Depends(_factory)):
    debts = ListDebtsUseCase(factory).execute()
    return [{"from": str(d.debtor_id), "to": str(d.creditor_id), "amount": str(d.amount)} for d in debts]


@router.post("/cycles/cancel")
def cancel_cycles(factory: UnitOfWorkFactory = Depends(_factory)):
    return CancelCyclesUseCase(factory).execute()


@router.get("/balances")
def get_balances(factory: UnitOfWorkFactory = Depends(_factory)):
    return GetBalancesUseCase(factory).execute()


# --- Отдача HTML ---
# Ищем файл index.html в папке templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "templates", "index.html")

@app.get("/")
def serve_frontend():
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return {"error": "Файл templates/index.html не найден. Создайте его."}

app.include_router(router)