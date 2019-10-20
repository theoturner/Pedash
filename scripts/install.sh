#!/bin/bash


sudo apt-get update
sudo apt-get install build-essential git python3
curl https://sh.rustup.rs -sSf | sh
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88
sudo add-apt-repository "deb https://repo.sovrin.org/sdk/deb bionic master"
sudo apt-get update
sudo apt-get install -y libnullpay libvcx

