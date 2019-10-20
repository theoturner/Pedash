#!/bin/bash

onred='\033[41m'
ongreen='\033[42m'
onyellow='\033[43m'
endcolor="\033[0m"

# Handle errors
set -e
error_report() {
    echo -e "${onred}Error: failed on line $1.$endcolor"
}
trap 'error_report $LINENO' ERR


if [[ "$OSTYPE" != "linux-gnu" ]]; then
    echo -e "${onred}OS not supported. Pedash runs on Linux.$endcolor"
fi

echo -e "${onyellow}Installing Pedash...$endcolor"

sudo apt-get update
sudo apt-get install build-essential git python3
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88
sudo add-apt-repository "deb https://repo.sovrin.org/sdk/deb bionic master"
sudo apt-get update
sudo apt-get install -y libnullpay libvcx

echo -e "${ongreen}Pedash installed.$endcolor"
