from fastapi import APIRouter, UploadFile, File
from services.verification_service import verification_instance, verification_metamodel, verification_schema

router = APIRouter()

@router.post("/metamodel")
async def check_metamodel(file: UploadFile = File(...)):
    return await verification_metamodel(file)

@router.post("/schema")
async def check_schema(file: UploadFile = File(...)):
    return await verification_schema(file)

@router.post("/instance")
async def check_instance(file: UploadFile = File(...)):
    return await verification_instance(file)