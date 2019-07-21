FROM jrcichra/smartcar_python_base
EXPOSE 8080
COPY requirements.txt /
RUN pip install -r /requirements.txt
CMD python -u controller.py