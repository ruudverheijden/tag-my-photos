# Tag My Photos

Self Hosted AI based Face Recognition of your Photo Library that writes EXIF/XMP tags to the photo.

Designed to run in parallel to other Photo Management tools (like Synology Photos, Immich, Piwigo, PhotoPrism or LibrePhotos) that often lack good Face Recognition capabilities. Since Tag My Photos does not change any folder structures but only adds some metadata tags to your photos, it can work seamless with any other photo management solution that can read EXIF/XMP tags. It's lightweight and doesn't require a GPU as it is designed to run on your local server / NAS through Docker.

## Principles

- Standalone: does not rely on anything outside a single Docker container (except a mounted volume)
- Single machine: designed to run on a single machine, like a local server or NAS
- CPU optimized: designed to also run on machines without a GPU
- Docker-based: so it can run anywhere
- API-first: any feature is exposed through APIs
- Non-Destructive: don't touch folder structures and backup + verify files when adding metadata 

## Architecture

- Python based, since Python offers a wide variety of AI / Face Recognition tools
- Using Prefect to run the data pipeline that outputs to a database
- Custom UI with FastAPI that interacts with the database to manually label recognized faces
- DeepFace for face recognition
- Containerize the whole application inside a single Docker container

## Data Processing Pipeline Overview

1. Detect new files on mounted volume
2. Store file metadata + hash in database
3. Detect Faces + create thumbnail of face area
4. Create Face Embeddings
5. Calculate distance of new faces to known clusters
6. Display newly found faces in GUI
7. User manually accepts or rejects matches
8. User manually bulk updates file metadata

## TODO

- Create task for parsing photo metadata
- Create Dockerfile containing
- Recognize faces:
  - Create Admin interface to view and accept proposals + manually tag
  - Recognition strategy: calculate distance between new photo and every face in a known Person. Suggest cluster with lowest average distance.

## Development

1. To build the Docker image:
`docker build . -t ruudv/tag-my-photos`

2. Place some photos in the 'photolibrary' folder of this project and run the container using:
`docker container run -p 4200:4200 -v ./photolibrary:/photolibrary ./data:/data ruudv/tag-my-photos`

## Run without Docker

1. Create a `.env` file containing:

    ```text
    DATA_PATH="/path/to/your/data/directory"
    LIBRARY_PATH="/path/to/your/photolibrary"
    DATABASE_PATH="${DATA_PATH}/tag-my-photos.db"
    THUMBNAIL_PATH="${DATA_PATH}/thumbnails"
    ```

2. Run `prefect server start` to start the Prefect Local Server running at `http://127.0.0.1:4200`

3. To run a specific Python script from the root directory use e.g. `python -m src.flows.initialize_database` or run the whole pipeline at once with `python -m src.flows.main`

4. Run the web interface via `flask --app src.web.main run` and browse to `http://127.0.0.1:5000`