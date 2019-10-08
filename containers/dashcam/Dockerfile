FROM jrcichra/smartcar_python_base
ARG commit
EXPOSE 8080
COPY . /
ENV READTHEDOCS True
RUN pip install -r /requirements.txt && echo -n $commit > /commit.txt
CMD python -u dashcam.py