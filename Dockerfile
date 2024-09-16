# Using base image from Prefect with latest tested Python version
FROM prefecthq/prefect:3.0.2-python3.12

# Create Volumes for both mounting the user's library and to persist data
VOLUME [ "/data" ]
VOLUME [ "/photolibrary" ]

# Set environment variables
ENV DATA_PATH="/data"
ENV LIBRARY_PATH="/photolibrary"

# Expose port 4200 used by Prefect
EXPOSE 4200

# Add our requirements.txt file to the image and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --trusted-host pypi.python.org --no-cache-dir

# Add flow scripts to the image
COPY src/flows /opt/prefect/flows

# Config needed to expose the Server properly
RUN prefect config set PREFECT_API_URL="http://127.0.0.1:4200/api"
RUN prefect config set PREFECT_SERVER_API_HOST="0.0.0.0"

# Start the Prefect Server and UI
ENTRYPOINT ["/opt/prefect/entrypoint.sh", "prefect", "server", "start"]