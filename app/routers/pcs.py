from fastapi import APIRouter, Depends, Request, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Cert, Person, PC, Service

import json


router = APIRouter(prefix="/pc", tags=["pc"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")



@router.get("/add", response_class=HTMLResponse)
async def add_pc_page(request: Request, db: Session = Depends(get_db)):
    pcs = db.query(PC).all()
    services = db.query(Service).all()
    certs = db.query(Cert).all()
    persons = db.query(Person).all()
    return templates.TemplateResponse("add_pc.html", {"request": request, "pcs": pcs, "services": services, "certs": certs, "persons": persons})


@router.get("/list_pc_partical", response_class=HTMLResponse)
async def list_pc_partical(request: Request, db: Session = Depends(get_db)):
    pcs = db.query(PC).all()
    return templates.TemplateResponse("list_pc_partical.html", {"request": request, "pcs": pcs})


@router.get("/edit/{id}")
async def edit_pc_get(id: int, db: Session = Depends(get_db)):
    pc = db.query(PC).get(id)
    if not pc:
        raise HTTPException(404, "PC not found")
    return {
        "id": id,
        "domain_name": pc.domain_name,
        "aud": pc.aud,
        "name": pc.name,
        "phone": pc.phone,
        "email": pc.email,
        "service":  [service.service_id for service in pc.service],
        "cert": [cert.cert_id for cert in pc.cert]
    }


@router.post("/add")
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

    new_pc = PC(domain_name=domain_name,
                           aud=aud,
                           name=name,
                           phone=phone,
                           email=email)
    serv = []
    cer = []
    for cservice in services:
        serv.append(db.query(Service).get(cservice))
    for ccert in certs:
        cer.append(db.query(Cert).get(ccert))
    new_pc.service.extend(serv)
    new_pc.cert.extend(cer)
    db.add(new_pc)
    db.commit()
    return RedirectResponse("/pc/add", status_code=303)


@router.put("/edit/{id}")
async def edit_pc(
        id: int,
        request: Request,
        db: Session = Depends(get_db)
):

    pc = db.query(PC).get(id)
    if not pc:
        return HTTPException(404, f"PC {id} not found")

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


    pc.domain_name = domain_name
    pc.aud = aud
    pc.name = name
    pc.phone = phone
    pc.email = email
    pc.service = db.query(Service).filter(Service.service_id.in_(services)).all()
    pc.cert = db.query(Cert).filter(Cert.cert_id.in_(certs)).all()

    db.commit()

    return {"success": True, "message": "Сертификат обновлен"}


@router.post("/delete")
async def delete_pc(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):

    deleted_pc = db.query(PC).get(id)
    if deleted_pc:
        db.delete(deleted_pc)
        db.commit()
    return RedirectResponse("/pc/add", status_code=303)
