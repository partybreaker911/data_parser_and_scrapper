# Use an appropriate base image for your web application
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Expose the port that your web application listens on
EXPOSE 5000

# Start the WSGI server (replace "app.py" with your main application file)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]