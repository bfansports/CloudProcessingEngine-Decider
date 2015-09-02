FROM python:2-onbuild
MAINTAINER SportArchive, Inc.

RUN mkdir -p /var/log/ct_deciders/

ENTRYPOINT ["python", "/usr/src/app/bin/decider.py"]
