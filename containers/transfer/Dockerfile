FROM jrcichra/smartcar_python_base
ARG commit
EXPOSE 8080
COPY requirements.txt /
RUN pip install -r /requirements.txt && apk add --update --no-cache openssh sshpass && echo -n $commit > /commit.txt
COPY . /
CMD python -u transfer.py