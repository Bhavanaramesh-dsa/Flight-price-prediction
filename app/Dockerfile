# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy dependency list and install packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt



# Copy the rest of the app
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000
ENV PYTHONPATH=/app
# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

