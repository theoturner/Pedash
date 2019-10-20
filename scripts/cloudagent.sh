#!/bin/bash

get_latest() {
    if [ ! -d $2 ]; then
        git clone https://github.com/$1/$2.git --recursive
        cd $2
    else
        cd $2
        git pull
    fi
    cd ..
}

curl https://sh.rustup.rs -sSf | sh
source $HOME/.cargo/env
get_latest hyperledger indy-sdk
cd indy-sdk/vcx/dummy-cloud-agent
cargo run ./config/sample-config.json
