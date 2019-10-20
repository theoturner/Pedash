import asyncio
import json
from ctypes import cdll
from time import sleep
import platform

import logging

from utils import file_ext
from vcx.api.connection import Connection
from vcx.api.credential import Credential
from vcx.api.disclosed_proof import DisclosedProof
from vcx.api.utils import vcx_agent_provision
from vcx.api.vcx_init import vcx_init_with_config
from vcx.state import State

# logging.basicConfig(level=logging.DEBUG) uncomment to get logs

provisionConfig = {
    'agency_url': 'http://localhost:8080',
    'agency_did': 'VsKV7grR1BUE29mG2Fm2kX',
    'agency_verkey': 'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
    'wallet_name': 'prover_wallet',
    'wallet_key': '123',
    'payment_method': 'null',
    'enterprise_seed': '000000000000000000000000Trustee1'
}

async def main():

    payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
    payment_plugin.nullpay_init()

    # Set up agent and VCX
    config = await vcx_agent_provision(json.dumps(provisionConfig))
    config = json.loads(config)
    config['institution_name'] = 'prover'
    config['institution_logo_url'] = 'http://robohash.org/2'
    config['genesis_path'] = 'genesis.txn'
    await vcx_init_with_config(json.dumps(config))

    # Input invitation details, connect to issuer and wait for them to issue a credential offer
    details = input('invite details: ')
    jdetails = json.loads(details)
    connection_to_issuer = await Connection.create_with_details('issuer', json.dumps(jdetails))
    await connection_to_issuer.connect('{"use_public_did": true}')
    await connection_to_issuer.update_state()
    sleep(10)
    offers = await Credential.get_offers(connection_to_issuer)

    # Create credential, send credential request and wait for credential offer from issuer
    # The issuer creates an IssuerCredential object and the prover creates a Credential object
    credential = await Credential.create('credential', offers[0])
    await credential.send_request(connection_to_issuer, 0)
    credential_state = await credential.get_state()
    while credential_state != State.Accepted:
        sleep(2)
        await credential.update_state()
        credential_state = await credential.get_state()

    # Wait for a proof request, create proof, fill with credentials from wallet, generate and send
    requests = await DisclosedProof.get_requests(connection_to_issuer)
    proof = await DisclosedProof.create('proof', requests[0])
    credentials = await proof.get_creds()
    for attr in credentials['attrs']:
        credentials['attrs'][attr] = {
            'credential': credentials['attrs'][attr][0]
        }
    await proof.generate_proof(credentials, {})
    await proof.send_proof(connection_to_issuer)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())