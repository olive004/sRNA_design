# A pre-req for using gpus here is the NVIDIA Docker Container Toolkit

sudo docker pull docker/dockerfile:1
sudo docker pull quay.io/biocontainers/intarna:3.4.1--pl5321hdcf5f25_0
# sudo docker pull nvidia/cuda:12.0.0-cudnn8-devel-ubuntu20.04
sudo docker pull nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04

# If image not built yet
sudo docker build -t srna2:latest docker_mufasa

cp ./requirements.txt ./docker_mufasa

sudo docker create -it \
--rm \
--gpus all \
--name srna2 \
--mount type=bind,source="$(pwd)",target=/workdir \
srna2:latest
sudo docker container start srna2
sudo docker exec -it srna2 bash docker_mufasa/post_install.sh
sudo docker exec -it srna2 /bin/bash 
# sudo docker container stop srna2
