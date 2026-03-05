from fastapi import APIRouter, Depends, Request, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Cert, Person

from app.utils import cert_info
from datetime import datetime
import json


router = APIRouter(prefix="/cert", tags=["cert"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@router.get("/add", response_class=HTMLResponse)
async def add_cert_page(request: Request, db: Session = Depends(get_db)):
    certs = db.query(Cert).all()
    persons = db.query(Person).all()
    return templates.TemplateResponse("add_cert.html", {"request": request, "certs": certs, "persons": persons})


@router.post("/file")
async def parse_cert(cert_file: UploadFile = File(...), db: Session = Depends(get_db)):
    cert = await cert_info.get_subject(cert_file)
    cert["filename"] = cert_file.filename

    person = db.query(Person).filter(Person.name == cert["subject"]).first()
    # print(person.person_id)
    try:
        cert["person_id"] = person.person_id
    except AttributeError:
        cert["person_id"] = None
    return cert


@router.get("/edit/{id}")
async def add_cert_page(id: int, db: Session = Depends(get_db)):
    cert = db.query(Cert).get(id)
    return {
        "name": cert.name,
        "version": cert.version,
        "date_from": f"{cert.date_from:%Y-%m-%d}",
        "date_to": f"{cert.date_to:%Y-%m-%d}",
        "person_id": cert.person_id,
        "org_id": cert.org_id,
        "thumbprint": cert.thumbprint
    }


@router.get("/list_cert_partical", response_class=HTMLResponse)
async def list_cert_partical(request: Request, db: Session = Depends(get_db)):
    certs = db.query(Cert).all()
    persons = db.query(Person).all()
    return templates.TemplateResponse("list_cert_partical.html", {"request": request, "certs": certs, "persons": persons})


@router.post("/add")
async def add_cert(
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        name = data["name"]
        version = data["version"]
        date_from = data["date_from"]
        date_to = data["date_to"]
        person_id = data["person_id"]
        org_id = data["org_id"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    new_cert = Cert(name=name,
                           version=version,
                           date_from=datetime.strptime(date_from, "%Y-%m-%d").date(),
                           date_to=datetime.strptime(date_to, "%Y-%m-%d").date(),
                           person_id=person_id,
                           org_id=org_id,
                           person=db.query(Person).get(person_id),
                    )
    db.add(new_cert)
    db.commit()
    return RedirectResponse("/add_cert", status_code=303)


@router.put("/edit/{id}")
async def edit_cert(
        id: int,
        request: Request,
        db: Session = Depends(get_db),

):
    cert = db.query(Cert).get(id)
    try:
        data = await request.json()
        cert.name = data["name"]
        cert.version = data["version"]
        cert.date_from = datetime.strptime(data["date_from"], "%Y-%m-%d").date(),
        cert.date_to = datetime.strptime(data["date_to"], "%Y-%m-%d").date(),
        cert.person_id = data["person_id"],
        cert.org_id = data["org_id"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    db.commit()
    return RedirectResponse("/add_cert", status_code=303)


@router.post("/delete")
async def delete_org(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db),

):
    deleted_cert = db.query(Cert).get(id)
    if deleted_cert:
        db.delete(deleted_cert)
        db.commit()
    return RedirectResponse("/add_cert", status_code=303)
