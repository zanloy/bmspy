FROM python:3.8.10-slim as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV REQUESTS_CA_BUNDLER /etc/ssl/certs/ca-certificates.crt

# Install VA certs
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates
COPY certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Updates for security concerns
RUN apt-get update && \
    apt-get -s dist-upgrade | grep "^Inst" | grep -i security | awk -F " " {'print $2'} | xargs apt-get install -y --no-install-recommends && \
    apt-get clean

FROM base AS python-deps

# Install our pip config file first
WORKDIR /code
COPY pip.conf .

# Install pipenv
RUN PIP_CONFIG_FILE=pip.conf pip install pipenv

# Install python deps in .venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 PIP_CONFIG_FILE=pip.conf pipenv install

FROM base as runtime

# Create a non-privileged user
RUN useradd --create-home app
WORKDIR /home/app
USER app

# Copy our virtual env
COPY --from=python-deps /code/.venv /home/app/.venv
ENV PATH="/home/app/.venv/bin:$PATH"

# Copy in our application
COPY app.py .

# Execute
#ENTRYPOINT ["python", "app.py"]
CMD [ "python", "app.py" ]