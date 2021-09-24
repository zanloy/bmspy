FROM python:3.8.10

WORKDIR /code

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --deploy

COPY app.py .

CMD [ "python", "app.py" ]