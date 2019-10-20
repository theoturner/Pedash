"""
Utilities for the issuer and prover plus a postgres wallet plugin
"""

import sys
import asyncio
import json
import random
from ctypes import cdll, CDLL
from time import sleep
import platform

import logging

from indy import wallet
from indy.error import ErrorCode, IndyError

from vcx.api.connection import Connection
from vcx.api.credential_def import CredentialDef
from vcx.api.issuer_credential import IssuerCredential
from vcx.api.credential import Credential
from vcx.api.proof import Proof
from vcx.api.disclosed_proof import DisclosedProof
from vcx.api.schema import Schema
from vcx.api.utils import vcx_agent_provision, vcx_messages_download
from vcx.api.vcx_init import vcx_init_with_config
from vcx.state import State, ProofState


async def create_schema_and_cred_def(schema_uuid, schema_name, schema_attrs, creddef_uuid, creddef_name):
    version = format("%d.%d.%d" % (random.randint(1, 101), random.randint(1, 101), random.randint(1, 101)))
    schema = await Schema.create(schema_uuid, schema_name, version, schema_attrs, 0)
    schema_id = await schema.get_schema_id()
    cred_def = await CredentialDef.create(creddef_uuid, creddef_name, schema_id, 0)
    cred_def_handle = cred_def.handle
    await cred_def.get_cred_def_id()
    cred_def_json = await cred_def.serialize()
    print(" >>> cred_def_handle", cred_def_handle)
    return cred_def_json


async def send_credential_request(my_connection, cred_def_json, schema_attrs, cred_tag, cred_name):
    cred_def = await CredentialDef.deserialize(cred_def_json)
    cred_def_handle = cred_def.handle
    print(" >>> cred_def_handle", cred_def_handle)
    credential = await IssuerCredential.create(cred_tag, schema_attrs, cred_def_handle, cred_name, '0')
    await credential.send_offer(my_connection)
    # serialize/deserialize credential - waiting for prover to respond with credential request
    credential_data = await credential.serialize()
    while True:
        my_credential = await IssuerCredential.deserialize(credential_data)
        await my_credential.update_state()
        credential_state = await my_credential.get_state()
        if credential_state == State.RequestReceived:
            break
        else:
            credential_data = await my_credential.serialize()
            sleep(2)
    await my_credential.send_credential(my_connection)
    # serialize/deserialize - waiting for prover to accept credential
    credential_data = await my_credential.serialize()
    while True:
        my_credential2 = await IssuerCredential.deserialize(credential_data)
        await my_credential2.update_state()
        credential_state = await my_credential2.get_state()
        if credential_state == State.Accepted:
            break
        else:
            credential_data = await my_credential2.serialize()
            sleep(2)


async def send_proof_request(my_connection, institution_did, proof_attrs, proof_uuid, proof_name, proof_predicates):
    proof = await Proof.create(proof_uuid, proof_name, proof_attrs, {}, requested_predicates=proof_predicates)
    await proof.request_proof(my_connection)
    # serialize/deserialize proof
    proof_data = await proof.serialize()
    while True:
        my_proof = await Proof.deserialize(proof_data)
        await my_proof.update_state()
        proof_state = await my_proof.get_state()
        if proof_state == State.Accepted:
            break
        else:
            proof_data = await my_proof.serialize()
            sleep(2)
    await my_proof.get_proof(my_connection)
    # Check proof is valid
    if my_proof.proof_state == ProofState.Verified:
        print("proof is verified!!")
    else:
        print("could not verify proof :(")


async def handle_messages(my_connection, handled_offers, handled_requests):
    offers = await Credential.get_offers(my_connection)
    for offer in offers:
        handled = False
        for handled_offer in handled_offers:
            if offer[0]['msg_ref_id'] == handled_offer['msg_ref_id']:
                print(">>> got back offer that was already handled", offer[0]['msg_ref_id'])
                handled = True
                break
        if not handled:
            save_offer = offer[0].copy()
            print(" >>> handling offer", save_offer['msg_ref_id'])
            await handle_credential_offer(my_connection, offer)
            handled_offers.append(save_offer)
    requests = await DisclosedProof.get_requests(my_connection)
    for request in requests:
        print("request", type(request), request)
        handled = False
        for handled_request in handled_requests:
            if request['msg_ref_id'] == handled_request['msg_ref_id']:
                print(">>> got back request that was already handled", request['msg_ref_id'])
                handled = True
                break
        if not handled:
            save_request = request.copy()
            print(" >>> handling proof", save_request['msg_ref_id'])
            await handle_proof_request(my_connection, request)
            handled_requests.append(save_request)


async def handle_credential_offer(my_connection, offer):
    credential = await Credential.create('credential', offer)
    await credential.send_request(my_connection, 0)
    # serialize/deserialize credential - wait for Issuer to send credential
    credential_data = await credential.serialize()
    while True:
        my_credential = await Credential.deserialize(credential_data)
        await my_credential.update_state()
        credential_state = await my_credential.get_state()
        if credential_state == State.Accepted:
            break
        else:
            credential_data = await my_credential.serialize()
            sleep(2)


async def handle_proof_request(my_connection, request):
    proof = await DisclosedProof.create('proof', request)
    credentials = await proof.get_creds()
    # Include self-attested attributes (not included in credentials)
    self_attested = {}
    # Use the first available credentials to satisfy the proof request
    for attr in credentials['attrs']:
        if 0 < len(credentials['attrs'][attr]):
            credentials['attrs'][attr] = {
                'credential': credentials['attrs'][attr][0]
            }
        else:
            self_attested[attr] = 'my self-attested value'
    for attr in self_attested:
        del credentials['attrs'][attr]
    print('credentials', credentials)
    print('self_attested', self_attested)
    await proof.generate_proof(credentials, self_attested)
    # FIXME possible segfault
    await proof.send_proof(my_connection)
    # serialize/deserialize proof
    proof_data = await proof.serialize()
    while True:
        my_proof = await DisclosedProof.deserialize(proof_data)
        await my_proof.update_state()
        proof_state = await my_proof.get_state()
        if proof_state == State.Accepted:
            break
        else:
            proof_data = await my_proof.serialize()
            sleep(2)
    print("proof_state", proof_state)


EXTENSION = {"darwin": ".dylib", "linux": ".so", "win32": ".dll", 'windows': '.dll'}


def file_ext():
    your_platform = platform.system().lower()
    return EXTENSION[your_platform] if (your_platform in EXTENSION) else '.so'


# load postgres dll and configure postgres wallet
def load_postgres_plugin(provisionConfig):
    print("Initializing postgres wallet")
    stg_lib = cdll.LoadLibrary("libindystrgpostgres" + file_ext())
    result = stg_lib.postgresstorage_init()
    if result != 0:
        print("Error unable to load postgres wallet storage", result)
        sys.exit(0)

    provisionConfig['wallet_type'] = 'postgres_storage'
    provisionConfig['storage_config'] = '{"url":"localhost:5432"}'
    provisionConfig['storage_credentials'] = '{"account":"postgres","password":"mysecretpassword","admin_account":"postgres","admin_password":"mysecretpassword"}'
    print("Success, loaded postgres wallet storage")


async def create_postgres_wallet(provisionConfig):
    print("Provision postgres wallet in advance")
    wallet_config = {
        'id': provisionConfig['wallet_name'],
        'storage_type': provisionConfig['wallet_type'],
        'storage_config': json.loads(provisionConfig['storage_config']),
    }
    wallet_creds = {
        'key': provisionConfig['wallet_key'],
        'storage_credentials': json.loads(provisionConfig['storage_credentials']),
    }
    try:
        await wallet.create_wallet(json.dumps(wallet_config), json.dumps(wallet_creds))
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    print("Postgres wallet provisioned")