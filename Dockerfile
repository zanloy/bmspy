FROM python:3.8.10-alpine3.13 as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1
ENV REQUESTS_CA_BUNDLER /etc/ssl/certs/ca-certificates.crt

# Install VA certs
RUN apk --no-cache add ca-certificates
COPY certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Updates for security concerns
RUN apk --no-cache upgrade

# Create unpriviledged user
RUN adduser -D bmspy
USER bmspy
WORKDIR /home/bmspy

FROM base AS runtime
ENV PATH="/home/bmspy/.local/bin:$PATH"

# Install our pip config file first
COPY pip.conf .

# Install pipenv
RUN PIP_CONFIG_FILE=pip.conf pip install pipenv

# Install python deps in .venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIP_CONFIG_FILE=pip.conf pipenv install

# Copy in our application
COPY . /home/bmspy/

# Execute
CMD [ "pipenv", "run", "python", "bmspy.py" ]