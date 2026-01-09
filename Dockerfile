FROM python:3.12-slim

# Create the directory structure
WORKDIR /usr/src

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY .env .env
COPY . .

# Set Python path to find app package
ENV PYTHONPATH=/usr/src

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]