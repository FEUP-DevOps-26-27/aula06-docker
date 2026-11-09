# Base image
FROM python:3.11-slim

# Setup working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY docker/training/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the training script to the working directory
COPY docker/training/train.py ./train.py

# Declare the volume mount point for models
VOLUME ["/app/models"]

# TODO: Set the command to run the training script
CMD []
