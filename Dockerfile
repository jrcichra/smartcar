FROM python:3.8.0-alpine
RUN apk add --no-cache --virtual .build-deps gcc musl-dev wireless-tools
COPY requirements.txt smartcarsocket.py common.py /
RUN pip install -r /requirements.txt
ARG commit
RUN echo -n $commit > /commit.txt