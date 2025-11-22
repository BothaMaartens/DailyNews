# --- Stage 1: Builder (Installing Python Dependencies) ---
# Use a slim Python image for a smaller build size
FROM python:3.11-slim as builder
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies needed for Django and Sphinx
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Image (Production Environment) ---
# Start fresh with the same base image
FROM python:3.11-slim
WORKDIR /app

# Set environment variables for Python, ensuring output is immediately visible
ENV PYTHONUNBUFFERED 1

# Expose the default Django port
EXPOSE 8000

# Copy installed packages from the builder stage
# This step significantly reduces the final image size by skipping build tools
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the entire project code (including Project_NewsApp, DailyNews_App, and the 'docs' folder)
COPY . /app/

# Set the default command to run the Django server
# 0.0.0.0 is crucial for accessibility within the container network
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]