# Pedash

Permissioned Data Sharing: a libvcx demo. Uses DIDs to permission access to data using verifiable credentials.

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
