#!/bin/sh

pip install jax==0.4.29
pip install jaxlib==0.4.29+cuda12.cudnn91 -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html 
pip install -U chex
pip install git+https://github.com/Steel-Lab-Oxford/core-bioreaction-simulation.git@47391ff32aa2e0e9dcbb4541efb526ff6c43e427#egg=bioreaction

# Install python3.10
apt update
apt upgrade
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa
apt update
apt install python3.10
apt install python3.10-venv
apt install python3.10-dev
ls -la /usr/bin/python3
rm /usr/bin/python3
ln -s python3.10 /usr/bin/python3
apt install curl
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
python3 --version
# python3.10 -m pip install ipython

pip install git+https://github.com/Steel-Lab-Oxford/core-bioreaction-simulation.git@47391ff32aa2e0e9dcbb4541efb526ff6c43e427#egg=bioreaction
pip install git+https://github.com/olive004/synbio_morpher.git@bc7aaf284fcf5b10abf591f5f2cf6c898f45861f#egg=synbio_morpher
# pip install -e src/bioreaction
pip install -r ./requirements.txt
