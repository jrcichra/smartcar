FROM python:3.8.0-alpine
RUN apk add --no-cache --virtual .build-deps gcc musl-dev wireless-tools
ADD requirements.txt /
RUN pip install -r /requirements.txt
ADD smartcarclient.py common.py /
ARG commit
RUN echo -n $commit > /commit.txt
CMD python smartcarclient.py