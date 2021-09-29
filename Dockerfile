FROM python:3.8.10-slim as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS python-deps

# Install pipenv
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Install python deps in .venv
WORKDIR /code
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

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