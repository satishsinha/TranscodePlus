import os
import time
from minio import Minio
from typing import Optional
from dotenv import load_dotenv
from minio.error import S3Error
from fastapi import UploadFile, HTTPException, APIRouter, Form


load_dotenv()

router = APIRouter()

# Load MinIO configuration from .env
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_SECURE = os.getenv("MINIO_SECURE") == "True"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

ALLOWED_BANNER_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.MOV'}
GENRES = {'Action', 'Drama', 'Comedy', 'Romantic', 'Sci-fi'}


def validate_file_extension(filename: str, allowed_extensions: set):
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions


@router.post("/upload/", tags=["Uploading & Transcoding Process"])
def upload_file_to_minio(
    banner_file: UploadFile,
    video_file: UploadFile,
    folder_name: str,
    title: str = Form(...),
    description: str = Form(...),
    genre: str = Form(...),
    trending: Optional[bool] = Form(None),
    new: Optional[bool] = Form(None)
):
    if genre not in GENRES:
        raise HTTPException(status_code=400, detail="Invalid genre. Choose from Action, Drama, Comedy, Romantic, Sci-fi.")

    try:
        # Ensure bucket exists
        if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
            minio_client.make_bucket(MINIO_BUCKET_NAME)

        # Validate file types
        if not validate_file_extension(banner_file.filename, ALLOWED_BANNER_EXTENSIONS):
            raise HTTPException(status_code=400, detail="Invalid banner file type. Only .jpg, .jpeg, and .png are allowed.")

        if not validate_file_extension(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
            raise HTTPException(status_code=400, detail="Invalid video file type. Only .mp4 is allowed.")

        # Prepare folder paths
        banner_path = f"{folder_name}/banner_{banner_file.filename}"
        video_path = f"{folder_name}/{video_file.filename}"

        # Start timing
        start_time = time.time()

        # Upload banner file in chunks
        banner_file.seek(0)
        banner_data = banner_file.file.read()
        banner_size = len(banner_data)
        banner_file.file.seek(0)  # Seek back to the beginning
        minio_client.put_object(
            MINIO_BUCKET_NAME,
            banner_path,
            banner_file.file,
            banner_size,
            content_type=banner_file.content_type
        )

        # Upload video file in chunks
        video_file.seek(0)
        video_data = video_file.file.read()
        video_size = len(video_data)
        video_file.file.seek(0)  # Seek back to the beginning
        minio_client.put_object(
            MINIO_BUCKET_NAME,
            video_path,
            video_file.file,
            video_size,
            content_type=video_file.content_type
        )

        # Calculate upload time
        upload_time = time.time() - start_time

        return {
            "status_code": 200,
            "message": "Files uploaded successfully",
            "folder_name": f"{folder_name}",
            "banner_s3_path": f"{MINIO_BUCKET_NAME}/{banner_path}",
            "video_s3_path": f"{MINIO_BUCKET_NAME}/{video_path}",
            "banner_uploaded_file_name": f"banner_{banner_file.filename}",
            "video_uploaded_file_name": video_file.filename,
            "title": title,
            "description": description,
            "genre": genre,
            "trending": trending,
            "new": new,
            "upload_time_seconds": upload_time
        }
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
