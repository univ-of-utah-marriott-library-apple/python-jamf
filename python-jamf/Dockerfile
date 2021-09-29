FROM python:3
RUN git clone https://github.com/magnusviri/python-jamf.git
WORKDIR python-jamf
RUN pip install -r requirements.txt
RUN pip install keyrings.alt
ENTRYPOINT /bin/bash