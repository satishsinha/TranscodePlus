import os
import subprocess
from minio import Minio
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import unquote
from fastapi import HTTPException, APIRouter

# Load environment variables
load_dotenv()

router = APIRouter()

# Configure MinIO client
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_SECURE") == "True"  # Use True or False based on your setup
)

# Store bucket name and resolutions folder in variables
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")
RESOLUTIONS_FOLDER = os.getenv("RESOLUTIONS_FOLDER")


@router.post("/transcode/", tags=["Uploading & Transcoding Process"])
def transcode_video(folder_name: str, filename: str, resolutions=None):
    if resolutions is None:
        resolutions = ["720p"]
    resolutions_list = [res.strip() for res in resolutions.split(",")]

    folder_name = unquote(folder_name)
    filename = unquote(filename)

    input_video = f"/tmp/{filename}"

    try:
        file_path = f"{folder_name}/{filename}"

        # Download input video from MinIO
        minio_client.fget_object(MINIO_BUCKET_NAME, file_path, input_video)

        # Initialize a dictionary to hold the output files information
        output_files = []

        # Define scales for different resolutions
        scales = {
            "144p": "256:144",
            "240p": "426:240",
            "360p": "640:360",
            "480p": "854:480",
            "720p": "1280:720",
            "1080p": "1920:1080"
        }

        for resolution in resolutions_list:
            if resolution not in scales:
                raise HTTPException(status_code=400, detail=f"Unsupported resolution: {resolution}")

            output_video = f"/tmp/{Path(filename).stem}_{resolution}.mp4"
            print(output_video)
            scale = scales[resolution]

            # Run FFmpeg to transcode the video
            subprocess.run([
                "ffmpeg", "-i", input_video,
                "-vf", f"scale={scale}", output_video
            ], check=True)

            # Upload transcoded video to MinIO in the specified folder
            minio_client.fput_object(
                MINIO_BUCKET_NAME,
                f"{folder_name}/{RESOLUTIONS_FOLDER}/{Path(output_video).name}",
                output_video
            )

            # Append information about the uploaded file
            output_files.append({
                "resolution": resolution,
                "s3_path": f"{MINIO_BUCKET_NAME}/{folder_name}/{RESOLUTIONS_FOLDER}/{Path(output_video).name}",
                "uploaded_file_name": Path(output_video).name
            })

            # Clean up local file
            os.remove(output_video)

        # Clean up the original file (commented out to preserve the original video)
        # os.remove(input_video)

        return {"status_code": 200, "message": "Videos transcoded and uploaded successfully", "files": output_files}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
