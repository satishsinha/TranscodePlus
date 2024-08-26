import os
import subprocess
from minio import Minio
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables
load_dotenv()

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


def transcode_video(filename: str, resolutions=None):
    if resolutions is None:
        resolutions = ["720p"]
    try:
        # Define paths for local temporary files
        input_video = f"/tmp/{filename}"

        # Download input video from MinIO
        minio_client.fget_object(MINIO_BUCKET_NAME, filename, input_video)

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

        for resolution in resolutions:
            if resolution not in scales:
                raise HTTPException(status_code=400, detail=f"Unsupported resolution: {resolution}")

            output_video = f"/tmp/{Path(filename).stem}_{resolution}.mp4"
            scale = scales[resolution]

            # Run FFmpeg to transcode the video
            subprocess.run([
                "ffmpeg", "-i", input_video,
                "-vf", f"scale={scale}", output_video
            ], check=True)

            # Upload transcoded video to MinIO in the specified folder
            minio_client.fput_object(
                MINIO_BUCKET_NAME,
                f"{RESOLUTIONS_FOLDER}/{Path(output_video).name}",
                output_video
            )

            # Append information about the uploaded file
            output_files.append({
                "resolution": resolution,
                "s3_path": f"{MINIO_BUCKET_NAME}/{RESOLUTIONS_FOLDER}/{Path(output_video).name}",
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
