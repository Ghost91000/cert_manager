from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.middleware.auth import AuthMiddleware
from app.routers import persons, login, certs, pcs, services, pc_parcer

from app.database import engine
from app.models import models

import app.utils.cert_info

from app.config import get_settings


settings = get_settings()

# 1. Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

# 2. Создаем приложение
app = FastAPI()

# 3. Настраиваем шаблоны
templates = Jinja2Templates(directory="./app/templates")

app.mount("/static", StaticFiles(directory="./app/static"), name="static")

app.add_middleware(AuthMiddleware)

app.include_router(persons.router)
app.include_router(login.router)
app.include_router(certs.router)
app.include_router(pcs.router)
app.include_router(services.router)
app.include_router(pc_parcer.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})