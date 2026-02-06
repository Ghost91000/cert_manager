from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from database import engine, get_db


# 1. Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

# 2. Создаем приложение
app = FastAPI()

# 3. Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")


# 4. Главная страница (просто показывает форму)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 5. Страница с формой добавления пользователя
@app.get("/add_person", response_class=HTMLResponse)
async def add_person_page(request: Request):
    return templates.TemplateResponse("add_person.html", {"request": request})


# 6. Обработка формы (когда нажимаешь "Добавить")
@app.post("/add_person")
async def add_person(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        phone: str = Form(...),
        db: Session = Depends(get_db)
):
    # Создаем нового пользователя
    new_person = models.Person(name=name, email=email, phone=phone)

    # Сохраняем в БД
    db.add(new_person)
    db.commit()
    db.refresh(new_person)

    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "message": f"Пользователь {name} добавлен!"
        }
    )


# 7. Показать всех пользователей
@app.get("/person", response_class=HTMLResponse)
async def show_person(request: Request, db: Session = Depends(get_db)):
    # Получаем всех пользователей из БД
    users = db.query(models.Person).all()

    return templates.TemplateResponse(
        "person.html",
        {
            "request": request,
            "users": users
        }
    )