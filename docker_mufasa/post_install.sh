#!/bin/sh

# pip install jax==0.4.29
# pip install jaxlib==0.4.29+cuda12.cudnn91 -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html 
pip install -U chex
# pip install git+https://github.com/Steel-Lab-Oxford/core-bioreaction-simulation.git@f903c39872de43e28b56653efda689bb082cb592#egg=bioreaction

# Install python3.11
apt update
apt autoremove
apt upgrade
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa
apt update
apt install python3.11
apt install python3.11-venv
apt install python3.11-dev
ls -la /usr/bin/python3
# rm /usr/bin/python3
# ln -s python3.11 /usr/bin/python3
# apt install curl
# curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
# python3 --version
# python3.11 -m pip install ipython

python3.11 -m pip install -U setuptools
export SETUPTOOLS_USE_DISTUTILS=stdlib
# python3.11 -m pip install git+https://github.com/Steel-Lab-Oxford/core-bioreaction-simulation.git@f903c39872de43e28b56653efda689bb082cb592#egg=bioreaction
python3.11 -m pip install git+https://github.com/olive004/synbio_morpher.git@bc7aaf284fcf5b10abf591f5f2cf6c898f45861f#egg=synbio_morpher
python3.11 -m pip install -e src/bioreaction
python3.11 -m pip install -r ./requirements.txt
