FROM python:3.6-alpine
ARG commit
RUN apk add --no-cache --virtual .build-deps gcc musl-dev && echo $commit > /commit.txt
COPY requirements.txt /
RUN pip install -r /requirements.txt
