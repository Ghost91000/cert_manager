from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import TelegramUser

from app.utils import tg_bot_alert


router = APIRouter(prefix="/telegram_alert", tags=["telegram_alert"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


tg_bot = tg_bot_alert.TelegramBot()


@router.get("/show", response_class=HTMLResponse)
async def get_tg_chats(request: Request, db: Session = Depends(get_db)):

    chats = tg_bot.get_chat_ids()
    for chat in chats:
        if db.query(TelegramUser).filter(TelegramUser.chat_id == chat["chat_id"]).first() is None:
            new_tg_user = TelegramUser(
                chat_id=chat["chat_id"],
                username=chat["username"],
                is_active=False
            )
            db.add(new_tg_user)
    db.commit()
    tg_users = db.query(TelegramUser).all()

    return templates.TemplateResponse("telegram_alert.html", {"request": request, "tg_users": tg_users})


@router.post("/update_alert")
async def update_tg_alert(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    for chat in data["chats"]:
        tg_user = db.query(TelegramUser).filter(TelegramUser.chat_id == chat).first()
        tg_user.is_active = True
        db.commit()
    return JSONResponse(content={"message": "Logged out"}, status_code=200)