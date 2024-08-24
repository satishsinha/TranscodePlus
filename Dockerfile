# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1  # Prevent Python from writing .pyc files to disk
ENV PYTHONUNBUFFERED 1  # Force Python to output to stdout and stderr without buffering


# Copy the rest of the application code into the container
COPY . /app

# Expose the port FastAPI will run on
EXPOSE 8001

# Command to run the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
