FROM jrcichra/karmen-python-client
ARG commit
EXPOSE 8080
COPY requirements.txt /
ENV READTHEDOCS True
RUN pip install -r /requirements.txt 
COPY . /
CMD python -u dashcam.py