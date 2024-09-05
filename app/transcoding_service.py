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
    resolutions_list = ("144p", "240p", "360p", "480p", "720p", "1080p")

    folder_name = unquote(folder_name)
    filename = unquote(filename)

    input_video = f"/tmp/{filename}"

    # Define scales for different resolutions
    scales = {
        "144p": (256, 144),
        "240p": (426, 240),
        "360p": (640, 360),
        "480p": (854, 480),
        "720p": (1280, 720),
        "1080p": (1920, 1080)
    }

    # Define a helper function to get the resolution from ffprobe output
    def get_video_resolution(video_path):
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=width,height", "-of", "csv=p=0", video_path
        ]
        output = subprocess.check_output(cmd).decode().strip().split('\n')

        # Extract width and height from the first line
        width, height = map(int, output[0].split(","))
        return width, height

    try:
        file_path = f"{folder_name}/{filename}"

        # Download input video from MinIO
        minio_client.fget_object(MINIO_BUCKET_NAME, file_path, input_video)

        # Get input video resolution
        input_width, input_height = get_video_resolution(input_video)

        # Filter resolutions that are lower than the input resolution
        valid_resolutions = [
            res for res, (width, height) in scales.items()
            if res in resolutions_list and width < input_width and height < input_height
        ]

        if not valid_resolutions:
            raise HTTPException(status_code=400, detail="No valid resolutions to transcode.")

        # Initialize a list to hold the output files information
        output_files = []

        for resolution in valid_resolutions:
            output_video = f"/tmp/{Path(filename).stem}_{resolution}.mp4"
            scale = f"scale={scales[resolution][0]}:{scales[resolution][1]}"

            # Run FFmpeg to transcode the video
            subprocess.run([
                "ffmpeg", "-i", input_video,
                "-vf", scale, output_video
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
