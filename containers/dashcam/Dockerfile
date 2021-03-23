FROM jrcichra/smartcar_python_base:${VERSION}
EXPOSE 8080
COPY requirements.txt /
ENV READTHEDOCS True
RUN pip3 install -r /requirements.txt 
COPY . /
CMD python -u dashcam.py