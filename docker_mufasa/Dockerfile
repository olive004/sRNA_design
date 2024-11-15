# syntax=docker/dockerfile:1

# https://quay.io/repository/biocontainers/intarna
FROM quay.io/biocontainers/intarna:3.4.1--pl5321hdcf5f25_0 AS intarna_build

FROM nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04 AS workdir_build
# FROM nvidia/cuda:12.0.0-cudnn8-devel-ubuntu20.04 AS workdir_build

################################################################################
#  Install python dependencies
################################################################################
WORKDIR /usr/lib
COPY ./requirements.txt /usr/lib/install_requirements/requirements.txt

# Install requirements
RUN apt-get update && \
    yes | apt-get install python3-pip
RUN yes | apt install git
RUN cd /usr/lib/install_requirements && \
    pip install -r ./requirements.txt 
# RUN pip install jax==0.4.13
RUN pip install jax==0.4.29
RUN pip install --upgrade "jax[cuda12_pip]" -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
RUN pip install git+https://github.com/Steel-Lab-Oxford/core-bioreaction-simulation.git@599990dcac56e7678f45269d2fc9df736d25f356#egg=bioreaction
RUN export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/cuda/lib64:/

################################################################################
#  Dependencies for https://github.com/hsalis/SalisLabCode/blob/master/mRNA_Stability_Calculator/Dockerfile
################################################################################

RUN apt-get update && apt-get install -y python3 python3-pip build-essential zip wget pypy graphviz nano \
                                         apt-transport-https ca-certificates curl software-properties-common \
                                         intel-mkl git-core cmake \
                                         pandoc memcached \
                                         gcc gfortran g++ openmpi-bin openmpi-common libopenmpi-dev libopenblas-base liblapack3 liblapack-dev make 
                                        #  && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/biointec/blamm.git && \
    cd blamm && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install

RUN wget https://www.tbi.univie.ac.at/RNA/download/sourcecode/2_5_x/ViennaRNA-2.5.0.tar.gz && \
    tar xvfz ViennaRNA-2.5.0.tar.gz && \
    cd ViennaRNA-2.5.0 && \
    ./configure && \
    make && \
    make install

################################################################################
#  setup environment
################################################################################
ENV ROOT_DIR=/workdir
ENV PYTHONPATH=/workdir
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV MNT=./..
WORKDIR /workdir

################################################################################
#  Copy IntaRNA dependencies
################################################################################
COPY --from=intarna_build /usr/local/bin/IntaRNA /usr/local/bin/
COPY --from=intarna_build /usr/local/include/IntaRNA /usr/local/include/
COPY --from=intarna_build /usr/local/lib/* /usr/local/lib/
