
# A pre-req for using gpus here is the NVIDIA Docker Container Toolkit

sudo docker pull quay.io/biocontainers/intarna:3.4.1--pl5321hdcf5f25_0
# sudo docker run --rm -it --entrypoint bash quay.io/biocontainers/intarna:3.4.1--pl5321hdcf5f25_0
sudo docker pull nvidia/cuda:12.6.0-cudnn-devel-ubuntu22.04

# If image not built yet
sudo docker build -t genetic_glitch:latest docker

cp ./requirements.txt ./docker

sudo docker create -it \
--rm \
--gpus all \
--name srna \
--runtime nvidia \
--mount type=bind,source="$(pwd)",target=/workdir \
genetic_glitch:latest
sudo docker container start srna
sudo docker exec -it srna bash docker/post_install.sh
sudo docker exec -it srna /bin/bash 
# sudo docker container stop srna
