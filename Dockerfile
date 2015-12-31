FROM python:2
MAINTAINER SportArchive, Inc.

RUN pip install -U pbr
COPY . /usr/src/app
RUN pip install -r /usr/src/app/requirements.txt

RUN mkdir -p /var/log/ct_deciders/ /var/tmp/logs/cpe/

ENTRYPOINT ["python", "/usr/src/app/bin/decider.py"]

