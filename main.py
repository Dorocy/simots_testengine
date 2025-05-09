from utils.response_handler import setup_exception_handlers
from fastapi import FastAPI

from routes.verification import router as verification_router


app = FastAPI()
app.include_router(verification_router, prefix="/verification")
setup_exception_handlers(app)