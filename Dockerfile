FROM python:3.12-alpine3.21 AS builder
LABEL maintainer="hugo.licea@gmail.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client libpq && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev && \
    /py/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /tmp/requirements.txt && \
    /py/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /tmp/requirements.dev.txt && \
    apk del .tmp-build-deps && \
    rm -rf /tmp

FROM python:3.12-alpine3.21
COPY --from=builder /py /py
COPY ./app /app
WORKDIR /app
EXPOSE 8000

RUN apk add --update --no-cache postgresql-client libpq && \
    adduser --disabled-password --no-create-home django-user

ENV PATH="/py/bin:$PATH"

USER django-user