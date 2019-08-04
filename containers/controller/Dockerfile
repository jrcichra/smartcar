FROM jrcichra/smartcar_python_base
ARG commit
EXPOSE 8080
COPY . /
COPY ../../../config.yml /
RUN pip install -r /requirements.txt && echo -n $commit > /commit.txt
CMD python -u controller.py