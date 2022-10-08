# coding=utf-8
import base64
import os

from OpenSSL import crypto
from aliyunsdkcore.auth import credentials

from alibaba_cloud_secretsmanager_client.auth.client_key_signer import ClientKeySigner
from alibaba_cloud_secretsmanager_client.utils import json_utils, env_const, const


def load_rsa_key_pair_credential_and_client_key_signer(client_key_path, password):
    client_key_info = json_utils.load(client_key_path)
    key_id = client_key_info.get("KeyId")
    private_key_data = client_key_info.get("PrivateKeyData")
    private_key_bytes = base64.decodebytes(bytes(private_key_data, 'utf-8'))
    pk12 = crypto.load_pkcs12(private_key_bytes, password)
    private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, pk12.get_privatekey()).decode()
    private_key = trim_private_key_pem(private_key)
    return credentials.RsaKeyPairCredential(key_id, private_key, 900), ClientKeySigner(key_id, private_key)


def trim_private_key_pem(private_key):
    prefix = "-----BEGIN PRIVATE KEY-----"
    newline = "\n"
    suffix = "-----END PRIVATE KEY-----"
    private_key = private_key.replace(prefix, "")
    private_key = private_key.replace(suffix, "")
    return private_key.replace(newline, "")


def get_password(config_dict, env_variable_name, file_path_name):
    password_from_env_variable = config_dict.get(env_variable_name)
    password = ""
    if password_from_env_variable is not None and password_from_env_variable != "":
        password = os.getenv(password_from_env_variable)
    if password is None or password == "":
        password_file_path = config_dict.get(file_path_name)
        if password_file_path is not None and password_file_path != "":
            with open(password_file_path) as f:
                password = f.read()
    if password is None or password == "":
        password = os.getenv(env_const.ENV_CLIENT_KEY_PASSWORD_NAME_KEY)
    if password is None or password == "":
        raise ValueError("client key password is not provided")
    return password
