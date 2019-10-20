import asyncio
import json
import random
from ctypes import cdll
from time import sleep
import platform

import logging

from utils import file_ext
from vcx.api.connection import Connection
from vcx.api.credential_def import CredentialDef
from vcx.api.issuer_credential import IssuerCredential
from vcx.api.proof import Proof
from vcx.api.schema import Schema
from vcx.api.utils import vcx_agent_provision
from vcx.api.vcx_init import vcx_init_with_config
from vcx.state import State, ProofState

# logging.basicConfig(level=logging.DEBUG) uncomment to get logs

# 'agency_url': URL of the agency
# 'agency_did':  public DID of the agency
# 'agency_verkey': public verkey of the agency
# 'wallet_name': name for newly created encrypted wallet
# 'wallet_key': encryption key for encoding wallet
# 'payment_method': method that will be used for payments
provisionConfig = {
  'agency_url':'http://localhost:8080',
  'agency_did':'VsKV7grR1BUE29mG2Fm2kX',
  'agency_verkey':'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
  'wallet_name':'issuer_wallet',
  'wallet_key':'123',
  'payment_method': 'null',
  'enterprise_seed':'000000000000000000000000Trustee1'
}


async def main():

    payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
    payment_plugin.nullpay_init()

    # Set up agent and VCX
    config = await vcx_agent_provision(json.dumps(provisionConfig))
    config = json.loads(config)
    config['institution_name'] = 'Issuer'
    config['institution_logo_url'] = 'http://robohash.org/1'
    config['genesis_path'] = 'genesis.txn'
    await vcx_init_with_config(json.dumps(config))

    # New schema and cred def
    version = format("%d.%d.%d" % (random.randint(1, 101), random.randint(1, 101), random.randint(1, 101)))
    schema = await Schema.create('schema_uuid', 'access schema', version, ['name', 'date', 'access'], 0)
    schema_id = await schema.get_schema_id()
    cred_def = await CredentialDef.create('credef_uuid', 'access', schema_id, 0)
    cred_def_handle = cred_def.handle
    await cred_def.get_cred_def_id()

    # Connect to prover, wait for them to accept (requires prover.py running)
    connection_to_prover = await Connection.create('prover')
    await connection_to_prover.connect('{"use_public_did": true}')
    await connection_to_prover.update_state()
    details = await connection_to_prover.invite_details(False)
    print(json.dumps(details))
    connection_state = await connection_to_prover.get_state()
    while connection_state != State.Accepted:
        sleep(2)
        await connection_to_prover.update_state()
        connection_state = await connection_to_prover.get_state()

    # Create credential and offer it to the prover, wait for them to make a credential request
    # The issuer creates an IssuerCredential object and the prover creates a Credential object
    schema_attrs = {
        'name': 'prover',
        'date': '01-2020',
        'access': 'yes',
    }
    credential = await IssuerCredential.create('prover_access', schema_attrs, cred_def_handle, 'cred', '0')
    await credential.send_offer(connection_to_prover)
    await credential.update_state()
    credential_state = await credential.get_state()
    while credential_state != State.RequestReceived:
        sleep(2)
        await credential.update_state()
        credential_state = await credential.get_state()

    # Send credential and wait for prover to receive it
    await credential.send_credential(connection_to_prover)
    await credential.update_state()
    credential_state = await credential.get_state()
    while credential_state != State.Accepted:
        sleep(2)
        await credential.update_state()
        credential_state = await credential.get_state()

    # Create proof and request it from the prover, wait for them to sen
    proof_attrs = [
        {'name': 'name', 'restrictions': [{'issuer_did': config['institution_did']}]},
        {'name': 'date', 'restrictions': [{'issuer_did': config['institution_did']}]},
        {'name': 'access', 'restrictions': [{'issuer_did': config['institution_did']}]}
    ]
    proof = await Proof.create('proof_uuid', 'proof_from_prover', proof_attrs, {})
    await proof.request_proof(connection_to_prover)
    proof_state = await proof.get_state()
    while proof_state != State.Accepted:
        sleep(2)
        await proof.update_state()
        proof_state = await proof.get_state()

    # Get and verify proof
    await proof.get_proof(connection_to_prover)
    if proof.proof_state == ProofState.Verified:
        print("proof is verified!!")
    else:
        print("could not verify proof.")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())