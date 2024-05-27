FROM python:3.10-slim

EXPOSE 8000

# Argument variables
ARG ENVIRONMENT
ARG ALLOWED_HOSTS
ARG SECRET_KEY
ARG DEBUG
ARG DB_HOST
ARG DB_NAME
ARG DB_PORT
ARG DB_USER
ARG DB_PASSWORD
ARG HOST_FE
ARG GROQ_API_KEY
ARG SENTRY_DSN

# Required environment variables as build arguments here
ENV ENVIRONMENT ${ENVIRONMENT}
ENV ALLOWED_HOSTS ${ALLOWED_HOSTS}
ENV SECRET_KEY ${SECRET_KEY}
ENV DEBUG ${DEBUG}
ENV DB_HOST ${DB_HOST}
ENV DB_NAME ${DB_NAME}
ENV DB_PORT ${DB_PORT}
ENV DB_USER ${DB_USER}
ENV DB_PASSWORD ${DB_PASSWORD}
ENV HOST_FE ${HOST_FE}
ENV GROQ_API_KEY ${GROQ_API_KEY}
ENV SENTRY_DSN ${SENTRY_DSN}

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt


WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--workers", "3", "--log-level", "debug", "--bind", "0.0.0.0:8000", "maams_be.wsgi"]
