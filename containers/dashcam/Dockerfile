FROM jrcichra/smartcar_python_base
ARG commit
ARG processor
EXPOSE 8080
COPY . /
RUN if [ "$processor" == "armv7l" ];then\
    pip install picamera    \
    fi
RUN pip install -r /requirements.txt && echo -n $commit > /commit.txt
CMD python -u dashcam.py