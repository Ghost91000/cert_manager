from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.database import get_db
from app.models.models import Person
from fastapi.responses import HTMLResponse, RedirectResponse
import json
from fastapi.staticfiles import StaticFiles


router = APIRouter(prefix="/person", tags=["persons"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@router.get("/add", response_class=HTMLResponse)
async def add_person_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(Person).all()
    return templates.TemplateResponse("add_person.html", {"request": request, "users": users})


@router.get("/edit/{id}")
async def add_person_page(id: int, db: Session = Depends(get_db)):
    user = db.query(Person).get(id)
    return {"name": user.name, "phone": user.phone, "email": user.email}


@router.get("/list_person_partical", response_class=HTMLResponse)
async def list_person_partical(request: Request, db: Session = Depends(get_db)):
    users = db.query(Person).all()
    return templates.TemplateResponse("list_person_partical.html", {"request": request, "users": users})


@router.post("/add")
async def add_person(
        request: Request,
        db: Session = Depends(get_db)
):

    try:
        data = await request.json()
        name = data["name"]
        phone = data["phone"]
        email = data["email"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")
    pers = db.query(Person).filter(Person.name == name).first()
    if pers:
        return {"code": 400, "person_id": pers.person_id}
    else:
        new_person = Person(name=name, email=email, phone=phone)
        # Сохраняем в БД
        db.add(new_person)
        db.commit()
        pers = db.query(Person).filter(Person.name == name).first()

    return {"person_id": pers.person_id, "name": pers.name}


@router.put("/edit/{id}")
async def edit_person(
        id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        name = data["name"]
        phone = data["phone"]
        email = data["email"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    person = db.query(Person).get(id)
    person.name = name
    person.phone = phone
    person.email = email

    db.commit()

    return RedirectResponse("person/add", status_code=303)


@router.post("/delete")
async def delete_person(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):
    deleted_person = db.query(Person).get(id)
    if deleted_person:
        db.delete(deleted_person)
        db.commit()
    return RedirectResponse("/person/add", status_code=303)
