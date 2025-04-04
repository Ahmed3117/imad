# Stage 1: Build stage
FROM python:3.9.18-alpine3.19 AS builder
# Install build dependencies
RUN apk update && \
    apk add --no-cache \
    build-base \
    mariadb-connector-c-dev \
    mariadb-dev \
    unixodbc-dev \
    gcc \
    libc-dev \
    musl-dev

# Set working directory
WORKDIR /app

# Copy requirements file
COPY app/requirements.txt /app/requirements.txt

# Install Python dependencies into /install directory
RUN pip install --upgrade pip
# Create the target directory
RUN mkdir -p /install
# Install packages to the /install directory
RUN pip install --target=/install -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.9.18-alpine3.19

# Install runtime dependencies
RUN apk update && \
    apk add --no-cache \
    mariadb-connector-c-dev \
    unixodbc-dev

# Set working directory
WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local/lib/python3.9/site-packages/

# Copy application code
COPY app/ /app

# Create a directory for static files source
COPY app/static /static_source

# Create volume for static files
VOLUME /app/static

# Remove build dependencies to reduce image size
RUN apk del build-base mariadb-dev gcc libc-dev musl-dev

# Modify entrypoint script to handle static files
COPY ./entrypoint.sh /

ENTRYPOINT ["sh", "/entrypoint.sh"]
