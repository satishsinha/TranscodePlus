# Build the Docker image
docker build -t transcoding-service:1.0 .

# run the Docker container for mac 
docker run -d --name transcodingService -p 8001:8001 -v /Applications/Dic_projects/projects/TranscodePlus:/app transcoding-service:1.0
