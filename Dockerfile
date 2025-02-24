# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt requirements.txt

# Install the Python libraries specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your project files into the container
COPY . .

# Expose the port that your WebSocket server will use (9080)
EXPOSE 9080

# Run the WebSocket server when the container starts
CMD ["python", "main2.py"]
