# syntax=docker/dockerfile:1

FROM quay.io/biocontainers/intarna:3.4.1--pl5321hdcf5f25_0 AS intarna_build

################################################################################
#  Install python dependencies
################################################################################
WORKDIR /usr/lib
COPY ./requirements.txt /usr/lib/install_requirements/requirements.txt
# RUN apt-get update && \
#     yes | apt-get install python3-pip
# RUN yes | apt install git
# RUN cd /usr/lib/install_requirements && \
#     pip install -r ./requirements.txt 

################################################################################
#  setup environment
################################################################################
ENV ROOT_DIR=/workdir
ENV PYTHONPATH=/workdir
ENV MNT=./..
WORKDIR /workdir
# ENTRYPOINT ["/bin/bash"]

################################################################################
#  Copy IntaRNA dependencies
################################################################################
# COPY /usr/local/bin/IntaRNA /usr/local/bin/
# COPY /usr/local/include/IntaRNA /usr/local/include/
# COPY /usr/local/lib/* /usr/local/lib/
# COPY --from=intarna_build /usr/lib/x86_64-linux-gnu/* /usr/lib/x86_64-linux-gnu/
