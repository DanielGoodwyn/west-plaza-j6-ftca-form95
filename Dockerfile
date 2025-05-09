# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY src/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code from src into the container at /app
COPY src/ .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
# Set FLASK_ENV to development for debugging, change to production for deployment
ENV FLASK_ENV=development 

# Ensure the data directory and its subdirectories are writable by the app user if needed
# RUN mkdir -p /app/data/filled_forms && chown -R python:python /app/data
# Note: Depending on how you run the container and manage volumes, 
# direct ownership changes might not be necessary or could be handled differently.

# Run app.py when the container launches
CMD ["flask", "run"] 
# Alternatively, for production, you might use a Gunicorn server:
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
