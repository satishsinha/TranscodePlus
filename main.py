from fastapi import FastAPI
from app.upload import router as upload_router
from app.transcoding_service import router as transcode_router
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],  # ["http://localhost:3001","https://adequate-renewed-hen.ngrok-free.app/"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Basic"])
def read_root():
    return {"Hello": "Welcome to Video Transcoding"}


app.include_router(upload_router)

app.include_router(transcode_router)
