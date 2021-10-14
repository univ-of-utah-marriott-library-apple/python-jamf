FROM python:3
WORKDIR python-jamf
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install keyrings.alt
ENTRYPOINT /bin/bash