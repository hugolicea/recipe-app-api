# Use the official Python image as the base image
FROM python:3.12-alpine3.21 AS builder
LABEL maintainer="hugo.licea@gmail.com"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy the requirements files to the /tmp directory
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

# Create a virtual environment and install dependencies
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev libpq && \
    apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev zlib zlib-dev linux-headers && \
    /py/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /tmp/requirements.txt && \
    /py/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /tmp/requirements.dev.txt && \
    apk del .tmp-build-deps && \
    rm -rf /tmp

# Use the official Python image as the base image for the final stage
FROM python:3.12-alpine3.21

# Copy the virtual environment from the builder stage
COPY --from=builder /py /py

# Copy the scripts directory to the /scripts directory
COPY ./scripts /scripts

# Copy the application code to the /app directory
COPY ./app /app

# Set the working directory to /app
WORKDIR /app

# Expose port 8000 for the application
EXPOSE 8000

# Install runtime dependencies
RUN apk add --update --no-cache postgresql-client libpq && \
    adduser --disabled-password --no-create-home django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

# Set the PATH environment variable to include the virtual environment
ENV PATH="/scripts:/py/bin:$PATH"

# Switch to the django-user user
USER django-user

# Command to run the application
CMD ["run.sh"]