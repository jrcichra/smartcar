FROM jrcichra/smartcar_python_base
ARG commit
EXPOSE 8080
COPY requirements.txt /
RUN pip install -r /requirements.txt && echo -n $commit > /commit.txt
COPY . /
CMD python -u gpio.py