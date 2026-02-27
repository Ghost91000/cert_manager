from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User

from app.middleware.hash_tokens import verify_password, create_access_token, create_refresh_token

from app.config import get_settings

settings = get_settings()


router = APIRouter(prefix="/auth", tags=["auth"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie(settings.COOKIE_NAME, path="/")
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/")
    return response


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2PasswordRequestForm автоматически достает из формы поля:
    - username
    - password
    """
    # 1. Ищем пользователя в БД
    user = db.query(User).filter(User.login == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        #raise HTTPException(400, "Неверный логин или пароль")
        return RedirectResponse(url="/auth/login", status_code=303)

    # 3. Создаем токен
    access_token = create_access_token(data={"sub": user.login})
    refresh_token = create_refresh_token(data={"sub": user.login})

    # УСТАНАВЛИВАЕМ COOKIE
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    # Refresh token — живет 7 дней
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )
    return response


# @app.post("/login")
# async def login_get(
#         username: str = Form(...),
#         password: str = Form(...),
#         db: Session = Depends(get_db)
# ):
#     existing_user = db.query(models.User).filter(models.User.login == username).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="already exist")
#
#     hashed_password = get_password_hash(password)
#     new_user = models.User(login=username, password=hashed_password)
#     db.add(new_user)
#     db.commit()
#
#     return {"msg": "yahoo"}