FROM jrcichra/smartcar_python_base
EXPOSE 8080
COPY . /
RUN pip install -r /requirements.txt
CMD python -u test_client.py