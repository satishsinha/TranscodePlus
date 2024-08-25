from fastapi import FastAPI, UploadFile, Form
from app.upload import upload_file_to_minio
from app.transcoding_service import transcode_video

app = FastAPI()


@app.get("/", tags=["Basic"])
def read_root():
    return {"Hello": "Welcome to Video Transcoding"}


@app.post("/upload/", tags=["Uploading & Transcoding Process"])
async def upload_video(file: UploadFile):
    # Upload the file
    upload_result = upload_file_to_minio(file, file.filename)
    return upload_result


@app.post("/transcode/", tags=["Uploading & Transcoding Process"])
async def transcode_video_endpoint(filename: str = Form(...), resolutions: str = Form(...)):
    # Split the resolutions string into a list
    resolution_list = [res.strip() for res in resolutions.split(',')]
    # Transcode the uploaded video
    transcoding_result = transcode_video(filename, resolution_list)
    return transcoding_result
