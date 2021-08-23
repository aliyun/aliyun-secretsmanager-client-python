import json

from alibaba_cloud_secretsmanager_client.model.client_key_credentials import ClientKeyCredential
from alibaba_cloud_secretsmanager_client.model.credentials_properties import CredentialsProperties
from alibaba_cloud_secretsmanager_client.model.region_info import RegionInfo
from aliyunsdkcore.auth import credentials

from alibaba_cloud_secretsmanager_client.utils import config_utils, const, env_const, client_key_utils


def check_config_param(param, param_name):
    if param == "" or param is None:
        raise ValueError("credentials config missing required parameters[%s]" % param_name)


def load_credentials_properties(file_name):
    if file_name is None or file_name == "":
        file_name = const.DEFAULT_CONFIG_NAME
    config_dict = config_utils.Properties(file_name).get_properties()
    credential = None
    region_info_list = []
    secret_name_list = []
    if config_dict is not None and len(config_dict) > 0:
        credentials_type = config_dict.get(env_const.ENV_CREDENTIALS_TYPE_KEY)
        access_key_id = config_dict.get(env_const.ENV_CREDENTIALS_ACCESS_KEY_ID_KEY)
        access_secret = config_dict.get(env_const.ENV_CREDENTIALS_ACCESS_SECRET_KEY)
        check_config_param(credentials_type, env_const.ENV_CREDENTIALS_TYPE_KEY)
        region_ids = config_dict.get(env_const.ENV_CACHE_CLIENT_REGION_ID_KEY)
        check_config_param(region_ids, env_const.ENV_CACHE_CLIENT_REGION_ID_KEY)
        try:
            region_dict_list = json.loads(region_ids)
            for region_dict in region_dict_list:
                region_info_list.append(RegionInfo(
                    None if region_dict.get(
                        env_const.ENV_REGION_REGION_ID_NAME_KEY) == '' else region_dict.get(
                        env_const.ENV_REGION_REGION_ID_NAME_KEY),
                    region_dict.get(env_const.ENV_REGION_VPC_NAME_KEY),
                    None if region_dict.get(
                        env_const.ENV_REGION_ENDPOINT_NAME_KEY) == '' else region_dict.get(
                        env_const.ENV_REGION_ENDPOINT_NAME_KEY)))
        except Exception:
            raise ValueError(
                ("config param.get(%s) is illegal" % env_const.ENV_CACHE_CLIENT_REGION_ID_KEY))
        if credentials_type == "ak":
            check_config_param(access_key_id, env_const.ENV_CREDENTIALS_ACCESS_KEY_ID_KEY)
            check_config_param(access_secret, env_const.ENV_CREDENTIALS_ACCESS_SECRET_KEY)
            credential = credentials.AccessKeyCredential(access_key_id, access_secret)
        elif credentials_type == "token":
            access_token_id = config_dict.get(env_const.ENV_CREDENTIALS_ACCESS_TOKEN_ID_KEY)
            access_token = config_dict.get(env_const.ENV_CREDENTIALS_ACCESS_TOKEN_KEY)
            check_config_param(access_token_id, env_const.ENV_CREDENTIALS_ACCESS_TOKEN_ID_KEY)
            check_config_param(access_token, env_const.ENV_CREDENTIALS_ACCESS_TOKEN_KEY)
            credential = credentials.AccessKeyCredential(access_token_id, access_token)
        elif credentials_type == "ram_role" or credentials_type == "sts":
            role_session_name = config_dict.get(env_const.ENV_CREDENTIALS_ROLE_SESSION_NAME_KEY)
            role_arn = config_dict.get(env_const.ENV_CREDENTIALS_ROLE_ARN_KEY)
            check_config_param(access_key_id, env_const.ENV_CREDENTIALS_ACCESS_KEY_ID_KEY)
            check_config_param(access_secret, env_const.ENV_CREDENTIALS_ACCESS_SECRET_KEY)
            check_config_param(role_session_name, env_const.ENV_CREDENTIALS_ROLE_SESSION_NAME_KEY)
            check_config_param(role_arn, env_const.ENV_CREDENTIALS_ROLE_ARN_KEY)
            credential = credentials.RamRoleArnCredential(access_key_id, access_secret,
                                                          role_arn, role_session_name)
        elif credentials_type == "ecs_ram_role":
            role_name = config_dict.get(env_const.ENV_CREDENTIALS_ROLE_NAME_KEY)
            check_config_param(role_name, env_const.ENV_CREDENTIALS_ROLE_NAME_KEY)
            credential = credentials.EcsRamRoleCredential(role_name)
        elif credentials_type == "client_key":
            client_key_path = config_dict.get(env_const.EnvClientKeyPrivateKeyPathNameKey)
            check_config_param(client_key_path, env_const.EnvClientKeyPrivateKeyPathNameKey)
            password = client_key_utils.get_password(config_dict)
            cred, signer = client_key_utils.load_rsa_key_pair_credential_and_client_key_signer(
                client_key_path, password)
            credential = ClientKeyCredential(signer, cred)
        else:
            raise ValueError(("config param.get(%s) is illegal" % env_const.ENV_CREDENTIALS_TYPE_KEY))
        secret_names = config_dict.get(const.PROPERTIES_SECRET_NAMES_KEY)
        if secret_names != "" and secret_names is not None:
            secret_name_list.extend(secret_names.split(","))
        credential_properties = CredentialsProperties(credential, secret_name_list, region_info_list, config_dict)
        return credential_properties
    return None
