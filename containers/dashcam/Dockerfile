FROM jrcichra/smartcar_python_base
ARG commit
EXPOSE 8080
COPY requirements.txt /
ENV READTHEDOCS True
RUN pip install -r /requirements.txt && echo -n $commit > /commit.txt
COPY . /
CMD python -u dashcam.py