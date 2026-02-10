from fastapi import FastAPI, Request, Form, Depends,  HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from datetime import datetime
import json

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


@app.get("/add_service", response_class=HTMLResponse)
async def add_service_page(request: Request, db: Session = Depends(get_db)):
    services = db.query(models.Org).all()
    return templates.TemplateResponse("add_service.html", {"request": request, "services": services})


@app.get("/list_service_partical", response_class=HTMLResponse)
async def list_service_partical(request: Request, db: Session = Depends(get_db)):
    services = db.query(models.Service).all()
    return templates.TemplateResponse("list_service_partical.html", {"request": request, "services": services})


@app.get("/add_pc", response_class=HTMLResponse)
async def add_pc_page(request: Request, db: Session = Depends(get_db)):
    pcs = db.query(models.PC).all()
    services = db.query(models.Service).all()
    certs = db.query(models.Cert).all()
    persons = db.query(models.Person).all()
    return templates.TemplateResponse("add_pc.html", {"request": request, "pcs": pcs, "services": services, "certs": certs, "persons": persons})


@app.get("/list_pc_partical", response_class=HTMLResponse)
async def list_pc_partical(request: Request, db: Session = Depends(get_db)):
    pcs = db.query(models.PC).all()
    return templates.TemplateResponse("list_pc_partical.html", {"request": request, "pcs": pcs})


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
        person_id: str = Form(...),
        org_id: str = Form(...),
        db: Session = Depends(get_db)
):
    new_cert = models.Cert(name=name,
                           version=version,
                           date_from=datetime.strptime(date_from, "%Y-%m-%d"),
                           date_to=datetime.strptime(date_to, "%Y-%m-%d"),
                           person_id=person_id,
                           org_id=org_id,
                           person=db.query(models.Person).get(person_id),
                           org=db.query(models.Org).get(org_id))
    db.add(new_cert)
    db.commit()
    return RedirectResponse("/add_cert", status_code=303)


@app.post("/delete_cert")
async def delete_org(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):
    deleted_cert = db.query(models.Cert).get(id)
    if deleted_cert:
        db.delete(deleted_cert)
        db.commit()
    return RedirectResponse("/add_cert", status_code=303)


@app.post("/add_service")
async def add_service(
        request: Request,
        name: str = Form(...),
        url: str = Form(...),
        db: Session = Depends(get_db)
):
    new_service = models.Service(name=name, url=url)
    # Сохраняем в БД
    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return RedirectResponse("/add_service", status_code=303)


@app.post("/delete_service")
async def delete_service(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):

    deleted_service = db.query(models.Service).get(id)
    if deleted_service:
        db.delete(deleted_service)
        db.commit()
    return RedirectResponse("/add_service", status_code=303)


@app.post("/add_pc")
async def add_pc(
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        domain_name = data["domain_name"]
        aud = data["aud"]
        name = data["name"]
        phone = data["phone"]
        email = data["email"]
        services = [int(id) for id in data["services"]]
        certs = [int(id) for id in data["certs"]]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    new_pc = models.PC(domain_name=domain_name,
                           aud=aud,
                           name=name,
                           phone=phone,
                           email=email)
    for cservice in services:
        new_pc.service.append(db.query(models.Service).get(cservice))
    for ccert in certs:
        new_pc.cert.append(db.query(models.Cert).get(ccert))
                          
    db.add(new_pc)
    db.commit()

    return RedirectResponse("/add_pc", status_code=303)


@app.post("/delete_pc")
async def delete_pc(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):

    deleted_cert = db.query(models.Cert).get(id)
    if deleted_cert:
        db.delete(deleted_cert)
        db.commit()
    return RedirectResponse("/add_cert", status_code=303)