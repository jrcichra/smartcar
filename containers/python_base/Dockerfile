FROM python:3.11.2-bullseye
RUN apt-get update && apt-get install -y git wireless-tools iputils-ping openssh-client sshpass expect && rm -rf /var/lib/apt/lists/*
ADD requirements.txt /
RUN pip3 install -r /requirements.txt
ADD common.py mockcamera.py mockgpio.py /
