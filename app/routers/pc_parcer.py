from fastapi import APIRouter, Request, File, UploadFile, Depends, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from typing import Annotated
from app.utils import cert_info, spec_check

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Cert, Person, PC

from datetime import datetime


router = APIRouter(prefix="/parcer", tags=["parcer"])
router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@router.post("/cert/{domain_name}/{user}")
async def cert(
    user: str,
    domain_name: str,
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
    db: Session = Depends(get_db)
):
    if len(files) == 0:
        return JSONResponse(status_code=status.HTTP_201_CREATED, content="No file was uploaded")

    for file in files:
        data = await cert_info.get_subject(file)
        pc = db.query(PC).filter(PC.domain_name == domain_name).first()
        cert = db.query(Cert).filter(Cert.thumbprint == data["thumbprint"]).first()
        if cert:
            cert.pc = [pc]
        else:
            person = db.query(Person).filter(Person.name == data["surname"] + " " + data["given_name"]).first()
            if person is None:
                person = Person(
                    name = data["surname"] + " " + data["given_name"],
                )
                db.add(person)

            new_cert = Cert(name=data["subject"],
                            date_from=data["date_from"],
                            date_to=data["date_to"],
                            thumbprint = data["thumbprint"],
                            org = data["issuer"],
                            certificate = await file.read(),
                            person_id = person.person_id,
                            person = person,
                            pc = [pc],
                            )
            db.add(new_cert)
        db.commit()
    return JSONResponse(status_code=status.HTTP_201_CREATED, content="File was uploaded")



@router.post("/pc/{domain_name}/{user}")
async def pc(user: str, domain_name: str, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    pc = db.query(PC).filter(PC.domain_name == domain_name).first()
    if pc:
        if pc.spec != data:
            history = spec_check.compare(pc.spec, data)
            pc.spec = data
            pc.timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            try:
                pc.spec_history = pc.spec_history + history
            except TypeError:
                pc.spec_history = history
        else:
            pc.timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    else:
        new_pc = PC(
            domain_name = domain_name,
            name = user,
            spec = data,
            timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
        )
        db.add(new_pc)
    db.commit()
    return JSONResponse(status_code=status.HTTP_201_CREATED, content="Spec uploaded")
