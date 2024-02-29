# Tag My Photos
Self Hosted AI based Face Recognition of your Photo Library that writes EXIF/XMP tags to the photo.

Designed to run in parallel to other Photo Management tools (like Synology Photos, Immich, Piwigo, PhotoPrism or LibrePhotos) that often lack good Face Recognition capabilities. Since Tag My Photos does not change any folder structures but only adds some metadata tags to your photos, it can work seamless with any other photo management solution that can read EXIF/XMP tags. It's lightweight and doesn't require a GPU as it is designed to run on your local server / NAS through Docker.

# Principles
- Standalone: does not rely on anything outside a single Docker container (except a mounted volume)
- Single machine: designed to run on a single machine, like a local server or NAS
- CPU optimized: designed to also run on machines without a GPU
- Docker-based: so it can run anywhere
- API-first: any feature is exposed through APIs
- Non-Destructive: don't touch folder structures and backup + verify files when adding metadata 

# Architecture
- Python based, since Python offers a wide variety of AI / Face Recognition tools
- Using Prefect to run the data pipeline that outputs to a database
- Custom UI with FastAPI that interacts with the database to manually label recognized faces
- DeepFace for face recognition
- Containerize the whole application inside a single Docker container

# Data Processing Pipeline Overview
1. Detect new files on mounted volume
2. Store file metadata + hash in database
3. Detect Faces + create thumbnail of face area
5. Create Face Embeddings
6. Calculate distance of new faces to known clusters
7. Display newly found faces in GUI
8. User manually accepts or rejects matches
9. User manually bulk updates file metadata

# TODO
- Create Prefect flow and task for reading photos
- Create task for parsing photo metadata
- Create thumbnails
- Create Dockerfile containing


# Development

1. To build the Docker image:
`docker build . -t ruudv/tag-my-photos`

2. Place some photos in the 'photolibrary' folder of this project and run the container using:
`docker container run -p 4200:4200 -v ./photolibrary:/photolibrary ./data:/data ruudv/tag-my-photos`

## Run without Docker
1. Create a `.env` file containing:
    ```text
    DATA_PATH="/path/to/your/data/directory"
    LIBRARY_PATH="/path/to/your/photolibrary"
    ```

2. Run `python main.py`