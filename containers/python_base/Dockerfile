FROM python:3.8.0-alpine
RUN apk add --no-cache --virtual .build-deps gcc musl-dev
COPY requirements.txt smartcarsocket.py /
RUN pip install -r /requirements.txt
ARG commit
RUN echo -n $commit > /commit.txt