ARG VERSION=latest
FROM jrcichra/smartcar_python_base:${VERSION}
COPY requirements.txt /
ENV READTHEDOCS True
RUN pip3 install -r /requirements.txt 
COPY . /
CMD python3 -u dashcam.py