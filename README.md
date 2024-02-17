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
- Using FastAPI for providing API support with async features
- SQLite database as it's simple and lightweight
- DeepFace for face recognition
- Containerize the whole application inside a single Docker container