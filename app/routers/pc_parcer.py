from fastapi import APIRouter, Request, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from typing import Annotated
from app.utils import cert_info

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
):
    print(f"{domain_name}/{user}")
    for file in files:
        data = await cert_info.get_subject(file)
        print(data["thumbprint"])



@router.post("/pc")
async def pc(request: Request):
    data = await request.json()
    print(data["motherboard"])
    print(data["cpu"])
    print(data["gpu"])
    print(data["ram"])
    print(data["storage"])
    print(data["timestamp"])

