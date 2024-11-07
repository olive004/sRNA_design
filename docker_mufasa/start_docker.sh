# A pre-req for using gpus here is the NVIDIA Docker Container Toolkit

sudo docker pull docker/dockerfile:1
sudo docker pull quay.io/biocontainers/intarna:3.3.2--pl5321h7ff8a90_0
# sudo docker pull nvidia/cuda:12.0.0-cudnn8-devel-ubuntu20.04
sudo docker pull nvidia/cuda:12.0.0-cudnn8-devel-ubuntu22.04

# If image not built yet
sudo docker build -t srna:latest docker_mufasa

cp ./requirements.txt ./docker_mufasa

sudo docker create -it \
--rm \
--gpus all \
--name srna \
--mount type=bind,source="$(pwd)",target=/workdir \
srna:latest
sudo docker container start srna
sudo docker exec -it srna bash docker_mufasa/post_install.sh
sudo docker exec -it srna /bin/bash 
# sudo docker container stop srna
