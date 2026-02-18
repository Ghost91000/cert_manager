from fastapi import FastAPI, Request, Form, Depends,  HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.base import BaseHTTPMiddleware

import models
from database import engine, get_db
from datetime import datetime, timedelta
import json
import cert_info
import os
from dotenv import load_dotenv

from auth import get_password_hash, verify_password, create_access_token, create_refresh_token
from jose import JWTError, jwt

#uvicorn main:app --reload --host 0.0.0.0

# 1. Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

# 2. Создаем приложение
app = FastAPI()

# 3. Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
COOKIE_NAME = os.getenv("COOKIE_NAME")
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))


# Схема для получения токена из заголовка Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next, db: Session = Depends(get_db)):
        #пропускаем всех по этим путям без проверки
        if request.url.path in ["/refresh", "/login"] or request.url.path.startswith("/static/"):
            return await call_next(request)

        access_token = request.cookies.get(COOKIE_NAME)
        refresh_token = request.cookies.get("refresh_token")

        # Пробуем проверить access token
        if access_token:
            try:
                jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
                # Токен валидный - просто идем дальше
                return await call_next(request)
            except JWTError:
                # Токен протух или битый - пробуем обновить
                pass
        # Если есть refresh token - обновляем прямо здесь!
        if refresh_token:
            try:
                # Проверяем refresh token
                refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                username = refresh_payload.get("sub")
                if username and db.query(models.User).filter(models.User.login == username).first():
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

                    print(f"🔄 Токен обновлен для {username}")
                    return response

            except JWTError:
                # Refresh протух - чистим куки
                print("❌ Refresh token протух")
                response = await call_next(request)
                response.delete_cookie("access_token", path="/")
                response.delete_cookie("refresh_token", path="/")
                return response
        # Нет токенов - просто выполняем (будет 401)
        print("⚠️ Нет токенов")
        return RedirectResponse(url="/login", status_code=303)


app.add_middleware(AuthMiddleware)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#===========================Login=======================================================================================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie(COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    return response


@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2PasswordRequestForm автоматически достает из формы поля:
    - username
    - password
    """
    # 1. Ищем пользователя в БД
    user = db.query(models.User).filter(models.User.login == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(400, "Неверный логин или пароль")

    # 3. Создаем токен
    access_token = create_access_token(data={"sub": user.login})
    refresh_token = create_refresh_token(data={"sub": user.login})

    # УСТАНАВЛИВАЕМ COOKIE
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    # Refresh token — живет 7 дней
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
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
#===========================LK==========================================================================================

@app.post("/get_tg_username/{username}")
async def get_tg_username(
        username: str,
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.login == username).first()

    return {"usernames": user.tg_alert}


@app.put("/edit_tg_username/{username}")
async def get_tg_username(
        request: Request,
        username: str,
        db: Session = Depends(get_db),
):
    data = await request.json()
    user = db.query(models.User).filter(models.User.login == username).first()
    user.tg_alert = data["usernames"]
    db.commit()
    return JSONResponse(content={"message": "Успешное обновление"})

#===========================Person======================================================================================


@app.get("/add_person", response_class=HTMLResponse)
async def add_person_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.Person).all()
    return templates.TemplateResponse("add_person.html", {"request": request, "users": users})


@app.get("/edit_person/{id}")
async def add_person_page(id: int, db: Session = Depends(get_db)):
    user = db.query(models.Person).get(id)
    return {"name": user.name, "phone": user.phone, "email": user.email}


@app.get("/list_person_partical", response_class=HTMLResponse)
async def list_person_partical(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.Person).all()
    return templates.TemplateResponse("list_person_partical.html", {"request": request, "users": users})

@app.post("/add_person")
async def add_person(
        request: Request,
        db: Session = Depends(get_db)
):

    try:
        data = await request.json()
        name = data["name"]
        phone = data["phone"]
        email = data["email"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")
    pers = db.query(models.Person).filter(models.Person.name == name).first()
    if pers:
        return {"code": 400, "person_id": pers.person_id}
    else:
        new_person = models.Person(name=name, email=email, phone=phone)
        # Сохраняем в БД
        db.add(new_person)
        db.commit()
        pers = db.query(models.Person).filter(models.Person.name == name).first()

    return {"person_id": pers.person_id, "name": pers.name}


@app.put("/edit_person/{id}")
async def edit_person(
        id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        name = data["name"]
        phone = data["phone"]
        email = data["email"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    person = db.query(models.Person).get(id)
    person.name = name
    person.phone = phone
    person.email = email

    db.commit()

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


#===========================Cert========================================================================================


@app.get("/add_cert", response_class=HTMLResponse)
async def add_cert_page(request: Request, db: Session = Depends(get_db)):
    certs = db.query(models.Cert).all()
    persons = db.query(models.Person).all()
    orgs = db.query(models.Org).all()
    return templates.TemplateResponse("add_cert.html", {"request": request, "certs": certs, "persons": persons, "orgs": orgs})


@app.post("/cert/file")
async def parse_cert(cert_file: UploadFile = File(...), db: Session = Depends(get_db)):
    cert = await cert_info.get_subject(cert_file)
    cert["filename"] = cert_file.filename

    person = db.query(models.Person).filter(models.Person.name == cert["subject"]).first()
    org = db.query(models.Org).filter(models.Org.name == cert["issuer"]).first()
    #print(person.person_id)
    try:
        cert["person_id"] = person.person_id
    except AttributeError:
        cert["person_id"] = None
    try:
        cert["org_id"] = org.org_id
    except AttributeError:
        cert["org_id"] = None
    return cert


@app.get("/edit_cert/{id}")
async def add_cert_page(id: int, db: Session = Depends(get_db)):
    cert = db.query(models.Cert).get(id)
    return {
        "name": cert.name,
        "version": cert.version,
        "date_from": f"{cert.date_from:%Y-%m-%d}",
        "date_to": f"{cert.date_to:%Y-%m-%d}",
        "person_id": cert.person_id,
        "org_id": cert.org_id,
    }


@app.get("/list_cert_partical", response_class=HTMLResponse)
async def list_cert_partical(request: Request, db: Session = Depends(get_db)):
    certs = db.query(models.Cert).all()
    persons = db.query(models.Person).all()
    orgs = db.query(models.Org).all()
    return templates.TemplateResponse("list_cert_partical.html", {"request": request, "certs": certs, "persons": persons, "orgs": orgs})


@app.post("/add_cert")
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

    new_cert = models.Cert(name=name,
                           version=version,
                           date_from=datetime.strptime(date_from, "%Y-%m-%d").date(),
                           date_to=datetime.strptime(date_to, "%Y-%m-%d").date(),
                           person_id=person_id,
                           org_id=org_id,
                           person=db.query(models.Person).get(person_id),
                           org=db.query(models.Org).get(org_id))
    db.add(new_cert)
    db.commit()
    return RedirectResponse("/add_cert", status_code=303)


@app.put("/edit_cert/{id}")
async def edit_cert(
        id: int,
        request: Request,
        db: Session = Depends(get_db),
        
):
    cert = db.query(models.Cert).get(id)
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


@app.post("/delete_cert")
async def delete_org(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db),
        
):
    deleted_cert = db.query(models.Cert).get(id)
    if deleted_cert:
        db.delete(deleted_cert)
        db.commit()
    return RedirectResponse("/add_cert", status_code=303)


#===========================PC==========================================================================================


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


@app.get("/edit_pc/{id}")
async def edit_pc_get(id: int, db: Session = Depends(get_db)):
    pc = db.query(models.PC).get(id)
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
    serv = []
    cer = []
    for cservice in services:
        serv.append(db.query(models.Service).get(cservice))
    for ccert in certs:
        cer.append(db.query(models.Cert).get(ccert))
    new_pc.service.extend(serv)
    new_pc.cert.extend(cer)
    db.add(new_pc)
    db.commit()
    return RedirectResponse("/add_pc", status_code=303)


@app.put("/edit_pc/{id}")
async def edit_pc(
        id: int,
        request: Request,
        db: Session = Depends(get_db)
):

    pc = db.query(models.PC).get(id)
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
    pc.service = db.query(models.Service).filter(models.Service.service_id.in_(services)).all()
    pc.cert = db.query(models.Cert).filter(models.Cert.cert_id.in_(certs)).all()

    db.commit()

    return {"success": True, "message": "Сертификат обновлен"}


@app.post("/delete_pc")
async def delete_pc(
        request: Request,
        id: str = Form(...),
        db: Session = Depends(get_db)
):

    deleted_pc = db.query(models.PC).get(id)
    if deleted_pc:
        db.delete(deleted_pc)
        db.commit()
    return RedirectResponse("/add_pc", status_code=303)


#===========================Org=========================================================================================


@app.get("/add_org", response_class=HTMLResponse)
async def add_org_page(request: Request, db: Session = Depends(get_db)):
    orgs = db.query(models.Org).all()
    return templates.TemplateResponse("add_org.html", {"request": request, "org": orgs})


@app.get("/list_org_partical", response_class=HTMLResponse)
async def list_org_partical(request: Request, db: Session = Depends(get_db)):
    orgs = db.query(models.Org).all()
    return templates.TemplateResponse("list_org_partical.html", {"request": request, "orgs": orgs})


@app.get("/edit_org/{id}")
async def edit_org_data(id:int, db: Session = Depends(get_db)):
    org = db.query(models.Org).get(id)
    return {"id": org.org_id, "name": org.name, "url": org.url}


@app.post("/add_org")
async def add_org(
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        new_org = models.Org(name=data["name"], url=data["url"])
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")
    org = db.query(models.Org).filter(models.Org.name == data["name"]).first()
    if org:
        return {"code": 400, "org_id": org.org_id}
    else:
        db.add(new_org)
        db.commit()
        org_new = db.query(models.Org).filter(models.Org.name == data["name"]).first()
    return {"code":201, "org_id": org_new.org_id, "name": org_new.name}


@app.put("/edit_org/{id}")
async def edit_org(
        id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    org = db.query(models.Org).get(id)
    try:
        data = await request.json()
        org.name = data["name"]
        org.url = data["url"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    db.commit()
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


#===========================Service=====================================================================================


@app.get("/add_service", response_class=HTMLResponse)
async def add_service_page(request: Request, db: Session = Depends(get_db)):
    services = db.query(models.Service).all()
    return templates.TemplateResponse("add_service.html", {"request": request, "services": services})


@app.get("/list_service_partical", response_class=HTMLResponse)
async def list_service_partical(request: Request, db: Session = Depends(get_db)):
    services = db.query(models.Service).all()
    return templates.TemplateResponse("list_service_partical.html", {"request": request, "services": services})

@app.get("/edit_service/{id}")
async def edit_service_get(id: int, db: Session = Depends(get_db)):
    services = db.query(models.Service).get(id)
    return {"name": services.name, "url": services.url}


@app.put("/edit_service/{id}")
async def edit_service(
        id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    service = db.query(models.Service).get(id)
    try:
        data = await request.json()
        service.name = data["name"]
        service.url = data["url"]
    except json.JSONDecodeError:
        raise HTTPException(400, "Невалидный JSON")

    db.commit()
    return RedirectResponse("/add_org", status_code=303)


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
