# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory.
WORKDIR /app

# Copy the requirements file and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose port 8000 for the webhook/health check endpoint.
EXPOSE 8000

# Run the bot.
CMD ["python", "bot/main.py"]
