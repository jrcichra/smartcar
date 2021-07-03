FROM python:3.7.9-alpine3.12
ADD requirements.txt /
RUN pip3 install -r /requirements.txt && apk add --update --no-cache openssh sshpass expect
ADD common.py /
