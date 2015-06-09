FROM python:2-onbuild
MAINTAINER SportArchive, Inc.

ENV AWS_ACCESS_KEY_ID xyz
ENV AWS_SECRET_ACCESS_KEY xyz
ENV AWS_CONFIG_BUCKET xyz
ENV AWS_CONFIG_KEY xyz

ENTRYPOINT ["python", "/usr/src/app/bin/decider.py"]
