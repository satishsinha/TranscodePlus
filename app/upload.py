from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

# Load MinIO configuration from .env
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_SECURE = os.getenv("MINIO_SECURE") == "True"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")  # Load bucket name from .env

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

def upload_file_to_minio(file: UploadFile, object_name: str):
    try:
        # Ensure bucket exists
        if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
            minio_client.make_bucket(MINIO_BUCKET_NAME)

        # Read file data
        file_data = file.file.read()
        if not file_data:
            raise HTTPException(status_code=400, detail="Empty file data")

        # Upload file to MinIO
        file.file.seek(0)  # Reset file pointer to the beginning
        minio_client.put_object(MINIO_BUCKET_NAME, object_name, file.file, len(file_data))

        return {
            "status_code": 200,
            "message": "File uploaded successfully",
            "s3_path": f"{MINIO_BUCKET_NAME}/{object_name}",
            "uploaded_file_name": object_name
        }
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"MinIO error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
