from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException, APIRouter
import os
from dotenv import load_dotenv

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
ALLOWED_VIDEO_EXTENSIONS = {'.mp4'}


def validate_file_extension(filename: str, allowed_extensions: set):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        return False
    return True


@router.post("/upload/", tags=["Uploading & Transcoding Process"])
def upload_file_to_minio(banner_file: UploadFile, video_file: UploadFile, folder_name: str):
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

        # Read and upload banner file
        banner_data = banner_file.file.read()
        if not banner_data:
            raise HTTPException(status_code=400, detail="Empty banner file data")
        banner_file.file.seek(0)
        minio_client.put_object(
            MINIO_BUCKET_NAME,
            banner_path,
            banner_file.file,
            len(banner_data),
            content_type=banner_file.content_type
        )

        # Read and upload video file
        video_data = video_file.file.read()
        if not video_data:
            raise HTTPException(status_code=400, detail="Empty video file data")
        video_file.file.seek(0)
        minio_client.put_object(
            MINIO_BUCKET_NAME,
            video_path,
            video_file.file,
            len(video_data),
            content_type=video_file.content_type
        )

        return {
            "status_code": 200,
            "message": "Files uploaded successfully",
            "banner_s3_path": f"{MINIO_BUCKET_NAME}/{banner_path}",
            "video_s3_path": f"{MINIO_BUCKET_NAME}/{video_path}",
            "banner_uploaded_file_name": banner_file.filename,
            "video_uploaded_file_name": video_file.filename
        }
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
