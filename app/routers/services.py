from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Service

import json


router = APIRouter(prefix="/service", tags=["service"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@router.get("/add", response_class=HTMLResponse)
async def add_service_page(request: Request, db: Session = Depends(get_db)):
    services = db.query(Service).all()
    return templates.TemplateResponse("add_service.html", {"request": request, "services": services})


@router.get("/list_service_partical", response_class=HTMLResponse)
async def list_service_partical(request: Request, db: Session = Depends(get_db)):
    services = db.query(Service).all()
    return templates.TemplateResponse("list_service_partical.html", {"request": request, "services": services})

@router.get("/edit/{id}")
async def edit_service_get(id: int, db: Session = Depends(get_db)):
    services = db.query(Service).get(id)
    return {"name": services.name, "url": services.url}


@router.put("/edit/{id}")
async def edit_service(
        id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    service = db.query(Service).get(id)
    try:
        data = await request.json()
        service.name = data["name"]
        service.url = data["url"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    db.commit()
    return RedirectResponse("/org/add", status_code=303)


@router.post("/add")
async def add_service(
        request: Request,
        name: str = Form(...),
        url: str = Form(...),
        db: Session = Depends(get_db)
):
    new_service = Service(name=name, url=url)
    # Сохраняем в БД
    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return RedirectResponse("/service/add", status_code=303)


@router.post("/delete")
async def delete_service(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):

    deleted_service = db.query(Service).get(id)
    if deleted_service:
        db.delete(deleted_service)
        db.commit()
    return RedirectResponse("/service/add", status_code=303)
