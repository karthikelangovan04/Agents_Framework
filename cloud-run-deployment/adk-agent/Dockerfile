# Use Python 3.12 slim image for better async context handling
# Python 3.12 has improved task context management which helps with MCP connections
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent.py .
COPY main.py .
COPY auth_helper.py .

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
