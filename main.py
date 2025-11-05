from api.response_handler import setup_exception_handlers
from fastapi import FastAPI
import uvicorn
from api.verification import router as verification_router


app = FastAPI(
    title="AAS 적합성 테스팅"
)
app.include_router(verification_router, prefix="/verification")
setup_exception_handlers(app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
