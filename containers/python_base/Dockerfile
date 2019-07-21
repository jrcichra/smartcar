FROM python:3.6-alpine
RUN apk add --no-cache --virtual .build-deps gcc musl-dev
COPY requirements.txt /
RUN pip install -r /requirements.txt
