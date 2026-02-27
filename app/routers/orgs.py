from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Org


import json


router = APIRouter(prefix="/org", tags=["org"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@router.get("/add", response_class=HTMLResponse)
async def add_org_page(request: Request, db: Session = Depends(get_db)):
    orgs = db.query(Org).all()
    return templates.TemplateResponse("add_org.html", {"request": request, "org": orgs})


@router.get("/list_org_partical", response_class=HTMLResponse)
async def list_org_partical(request: Request, db: Session = Depends(get_db)):
    orgs = db.query(Org).all()
    return templates.TemplateResponse("list_org_partical.html", {"request": request, "orgs": orgs})


@router.get("/edit_org/{id}")
async def edit_org_data(id:int, db: Session = Depends(get_db)):
    org = db.query(Org).get(id)
    return {"id": org.org_id, "name": org.name, "url": org.url}


@router.post("/add")
async def add_org(
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        new_org = Org(name=data["name"], url=data["url"])
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")
    org = db.query(Org).filter(Org.name == data["name"]).first()
    if org:
        return {"code": 400, "org_id": org.org_id}
    else:
        db.add(new_org)
        db.commit()
        org_new = db.query(Org).filter(Org.name == data["name"]).first()
    return {"code":201, "org_id": org_new.org_id, "name": org_new.name}


@router.put("/edit/{id}")
async def edit_org(
        id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    org = db.query(Org).get(id)
    try:
        data = await request.json()
        org.name = data["name"]
        org.url = data["url"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    db.commit()
    return RedirectResponse("/org/add", status_code=303)


@router.post("/delete")
async def delete_org(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):
    deleted_org = db.query(Org).get(id)
    if deleted_org:
        db.delete(deleted_org)
        db.commit()
    return RedirectResponse("/org/add", status_code=303)
