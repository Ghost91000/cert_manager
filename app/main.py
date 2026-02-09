from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from database import engine, get_db

#uvicorn main:app --reload

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
async def add_person_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.Person).all()
    return templates.TemplateResponse("add_person.html", {"request": request, "users": users})


@app.get("/list_person_partical", response_class=HTMLResponse)
async def list_person_partical(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.Person).all()
    return templates.TemplateResponse("list_person_partical.html", {"request": request, "users": users})


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

    return RedirectResponse("/add_person", status_code=303)


@app.post("/delete_person")
async def delete_person(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):
    deleted_person = db.query(models.Person).get(id)
    if deleted_person:
        db.delete(deleted_person)
        db.commit()
    return RedirectResponse("/add_person", status_code=303)


@app.get("/add_cert", response_class=HTMLResponse)
async def add_cert_page(request: Request, db: Session = Depends(get_db)):
    certs = db.query(models.Cert).all()
    persons = db.query(models.Person).all()
    orgs = db.query(models.Org).all()
    return templates.TemplateResponse("add_cert.html", {"request": request, "certs": certs, "persons": persons, "orgs": orgs})

@app.get("/list_cert_partical", response_class=HTMLResponse)
async def list_cert_partical(request: Request, db: Session = Depends(get_db)):
    certs = db.query(models.Cert).all()
    persons = db.query(models.Person).all()
    orgs = db.query(models.Org).all()
    return templates.TemplateResponse("list_cert_partical.html", {"request": request, "certs": certs, "persons": persons, "orgs": orgs})

@app.get("/add_org", response_class=HTMLResponse)
async def add_org_page(request: Request, db: Session = Depends(get_db)):
    orgs = db.query(models.Org).all()
    return templates.TemplateResponse("add_org.html", {"request": request, "org": orgs})


@app.get("/list_org_partical", response_class=HTMLResponse)
async def list_org_partical(request: Request, db: Session = Depends(get_db)):
    orgs = db.query(models.Org).all()
    return templates.TemplateResponse("list_org_partical.html", {"request": request, "orgs": orgs})

@app.post("/add_org")
async def add_org(
        request: Request,
        name: str = Form(...),
        url: str = Form(...),
        db: Session = Depends(get_db)
):
    new_org = models.Org(name=name, url=url)
    # Сохраняем в БД
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    return RedirectResponse("/add_org", status_code=303)


@app.post("/delete_org")
async def delete_org(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):

    deleted_org = db.query(models.Org).get(id)
    if deleted_org:
        db.delete(deleted_org)
        db.commit()
    return RedirectResponse("/add_org", status_code=303)


@app.post("/add_cert")
async def add_cert(
        name: str = Form(...),
        version: str = Form(...),
        date_from: str = Form(...),
        date_to: str = Form(...),
        person: str = Form(...),
        org: str = Form(...),
        db: Session = Depends(get_db)
):
    print(date_from)
    #new_cert = models.Org(name=name, version=version, date_from=date_from, date_to=date_to, person=person, org=org)
    # Сохраняем в БД
    #db.add(new_cert)
    #db.commit()
    #db.refresh(new_cert)

    return RedirectResponse("/add_cert", status_code=303)


@app.post("/delete_cert")
async def delete_org(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):

    deleted_org = db.query(models.Org).get(id)
    if deleted_org:
        db.delete(deleted_org)
        db.commit()
    return RedirectResponse("/add_org", status_code=303)