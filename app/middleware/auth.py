from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from app.database import SessionLocal
from app.models.models import User

from app.middleware.hash_tokens import create_access_token, create_refresh_token
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        #пропускаем всех по этим путям без проверки
        if request.url.path in ["/auth/login"] or request.url.path.startswith(("/static/", '/parcer/')):
            return await call_next(request)

        access_token = request.cookies.get(settings.COOKIE_NAME)
        refresh_token = request.cookies.get("refresh_token")
        db = SessionLocal()
        # Пробуем проверить access token
        if access_token:
            try:
                jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                # Токен валидный - просто идем дальше
                return await call_next(request)
            except JWTError:
                # Токен протух или битый - пробуем обновить
                pass
        # Если есть refresh token - обновляем прямо здесь!
        if refresh_token:
            try:
                # Проверяем refresh token
                refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                username = refresh_payload.get("sub")
                if username and db.query(User).filter(User.login == username).first():
                    # Создаем новые токены
                    new_access = create_access_token({"sub": username})
                    new_refresh = create_refresh_token({"sub": username})
                    # Выполняем запрос
                    response = await call_next(request)

                    # Обновляем куки
                    response.set_cookie(
                        key="access_token",
                        value=new_access,
                        httponly=True,
                        max_age=900,  # 15 минут
                        path="/"
                    )
                    response.set_cookie(
                        key="refresh_token",
                        value=new_refresh,
                        httponly=True,
                        max_age=604800,  # 7 дней
                        path="/"
                    )

                    print(f"? Токен обновлен для {username}")
                    return response

            except JWTError:
                # Refresh протух - чистим куки
                print("? Refresh token протух")
                response = await call_next(request)
                response.delete_cookie("access_token", path="/")
                response.delete_cookie("refresh_token", path="/")
                return response
        # Нет токенов - просто выполняем (будет 401)
        print("?? Нет токенов")
        return RedirectResponse(url="/auth/login", status_code=303)
