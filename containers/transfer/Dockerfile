ARG VERSION=latest
FROM jrcichra/smartcar_python_base:${VERSION}
EXPOSE 8080
COPY requirements.txt /
RUN pip install -r /requirements.txt && apk add --update --no-cache openssh sshpass expect
COPY . /
CMD python -u transfer.py