FROM jrcichra/smartcar_python_base
ARG commit
EXPOSE 8080
COPY . /
RUN pip install -r /requirements.txt && echo -n $commit > /commit.txt
CMD "python -u transfer.py" 