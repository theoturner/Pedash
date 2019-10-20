# Pedash

Permissioned Data Sharing. Uses DIDs to permission access to data using verifiable credentials.

## Install

Pedash runs on Linux. Install:

```Bash
./scripts/install.sh
```

## Usage

Pedash must be pointed at a Hyperledger Indy VCX-compatible agent. Get and run a local VCX agent:

```Bash
./scripts/cloudagent.sh
```

Hyperledger Indy testnet, mainnet and even permissioned independent deployments can easily be configured by changin the genesis transaction file. Simply place the genesis transaction in `pedash/genesis.txn`. See the Hyperledger Indy [docs](https://hyperledger-indy.readthedocs.io/projects/node/en/latest/transactions.html#genesis-transactions) for which transaction to use for which network (including creating your own). By default, Pedash is configured for a local deployment - no need to change the file.