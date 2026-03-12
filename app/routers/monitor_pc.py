from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Cert,  PC


router = APIRouter(prefix="/monitor_pc", tags=["monitor_pc"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@router.get("/show/tree", response_class=HTMLResponse)
async def add_pc_page(request: Request, db: Session = Depends(get_db)):
    pcs = db.query(PC).all()
    certs = db.query(Cert).all()
    return templates.TemplateResponse("pc_cert_tree.html", {"request": request, "pcs": pcs, "certs": certs})
