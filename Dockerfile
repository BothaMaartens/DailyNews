# --- Stage 1: BUILDER (Installing Python Dependencies and build tools) ---
# Use a slim Python image for a smaller build size
FROM python:3.11-slim AS builder
WORKDIR /app

# Install system dependencies required to compile certain Python packages (e.g., database drivers)
# The packages are installed and then immediately removed to keep the image clean
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    pkg-config \
    default-libmysqlclient-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies needed for Django and Sphinx
RUN pip install -v --no-cache-dir -r requirements.txt

# --- Stage 2: FINAL IMAGE (Production Environment) ---
# Start fresh with the same base image
FROM python:3.11-slim
WORKDIR /app

# Install the REQUIRED MySQL/MariaDB runtime library
RUN apt-get update && apt-get install -y \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables (fixed syntax: ENV key=value)
ENV PYTHONUNBUFFERED=1

# Expose the default Django port
EXPOSE 8000

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the entire project code (including Project_NewsApp, DailyNews_App, and the 'docs' folder)
COPY . /app/

# Set the default command to run the Django server
# Use 0.0.0.0 to make the server accessible from outside the container's localhost
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]