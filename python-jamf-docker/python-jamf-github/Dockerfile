FROM python:3
RUN git clone https://github.com/univ-of-utah-marriott-library-apple/python-jamf
WORKDIR python-jamf
RUN git checkout main && \
    git describe --tags > jamf/VERSION && \
    pip install -r requirements.txt && \
    pip install keyrings.alt && \
    python setup.py install
ENTRYPOINT /bin/bash