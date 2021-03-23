ARG VERSION=latest
FROM jrcichra/smartcar_python_base:${VERSION}
EXPOSE 8080
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY . /
CMD python -u gpio.py