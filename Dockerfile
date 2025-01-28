FROM python:3.12-alpine3.21
LABEL maintainer="hugo.licea@gmail.com"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py

RUN /py/bin/pip install --upgrade pip

# Debug step to check the contents of requirements.txt
RUN cat /tmp/requirements.txt

# Debug step to check the Python and pip versions
RUN /py/bin/python --version && /py/bin/pip --version

RUN /py/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /tmp/requirements.txt
RUN if [ "$DEV" = "true" ]; then /py/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /tmp/requirements.dev.txt; fi

RUN rm -rf /tmp

RUN adduser \
    --disabled-password \
    --no-create-home \
    django-user

ENV PATH="/py/bin:$PATH"

USER django-user