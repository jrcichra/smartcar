FROM jrcichra/smartcar_python_base
ARG commit
EXPOSE 8080
COPY . /
RUN pip install -r /requirements.txt && echo $commit -n > /commit.txt
CMD python -u test_client.py