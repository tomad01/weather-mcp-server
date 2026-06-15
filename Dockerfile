FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy project metadata and lock file
COPY . . 

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt 

# Expose MCP port
EXPOSE 8001

# Start the MCP server
CMD ["python", "server_sse.py"]