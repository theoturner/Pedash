#!/bin/bash

if [[ "$OSTYPE" != "linux-gnu" ]]; then
    echo "OS not supported. Pedash runs on Linux."
fi

sudo apt-get update
sudo apt-get install build-essential git python3
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88
sudo add-apt-repository "deb https://repo.sovrin.org/sdk/deb bionic master"
sudo apt-get update
sudo apt-get install -y libnullpay libvcx

