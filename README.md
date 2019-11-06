# Pedash

Permissioned Data Sharing: a [libvcx](https://github.com/hyperledger/indy-sdk/tree/master/vcx) demo. Uses DIDs to permission access to data using verifiable credentials.

This software is licensed under the Apache 2.0 software license (see LICENSE file). Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

The author of this software makes no representation or guarantee that this software (including any third-party libraries) will perform as intended or will be free of errors, bugs or faulty code. The software may fail which could completely or partially limit functionality or compromise computer systems. If you use or implement the software, you do so at your own risk. In no event will the author of this software be liable to any party for any damages whatsoever, even if it had been advised of the possibility of damage.

## Install

Pedash runs on Linux. Install:

```Bash
./scripts/install.sh
```

## Setup

Pedash must be pointed at a Hyperledger Indy pool and cloud agent. Get and run a local copy of both:

```Bash
./scripts/cloudagent.sh
```

Hyperledger Indy testnet, mainnet and even permissioned independent deployments can easily be configured by changin the genesis transaction file. Simply place the genesis transaction in `pedash/genesis.txn`. See the Hyperledger Indy [docs](https://hyperledger-indy.readthedocs.io/projects/node/en/latest/transactions.html#genesis-transactions) for which transaction to use for which network (including creating your own). By default, Pedash is configured for a local deployment - no need to change the file.

## Usage

The demo sets up a secure channel between a credential issuer (database owner) and a prover (accessor). After setup, there is an E2E pairwise encrypted channel between the two. The issuer sends a credential for accessing the permissioned database to the accessor.

Terminal 1:

```Bash
cd pedash
python3 issuer.py
```

Terminal 2:

```Bash
cd pedash
python3 prover.py
```

Note for WSL users: install docker in the Windows environment, then connect to it in WSL.

