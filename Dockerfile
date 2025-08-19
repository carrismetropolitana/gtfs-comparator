# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements if exists, then install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy the comparator script and any other needed files
COPY gtfs-comparator.py ./

# Set default command to run the script
CMD ["python", "gtfs-comparator.py"]