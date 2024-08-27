from fastapi import FastAPI
from app.upload import router as upload_router
from app.transcoding_service import router as transcode_router

app = FastAPI()


@app.get("/", tags=["Basic"])
def read_root():
    return {"Hello": "Welcome to Video Transcoding"}


app.include_router(upload_router)

app.include_router(transcode_router)
