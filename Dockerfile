FROM python:2-onbuild
MAINTAINER SportArchive, Inc.
ENTRYPOINT ["python", "bin/ct-decider.py"]
