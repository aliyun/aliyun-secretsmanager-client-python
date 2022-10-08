import json

from aliyunsdkcore.auth import credentials

from alibaba_cloud_secretsmanager_client.model.client_key_credentials import ClientKeyCredential
from alibaba_cloud_secretsmanager_client.model.credentials_properties import CredentialsProperties
from alibaba_cloud_secretsmanager_client.model.dkms_config import DKmsConfig
from alibaba_cloud_secretsmanager_client.model.region_info import RegionInfo
from alibaba_cloud_secretsmanager_client.utils import config_utils, const, env_const, client_key_utils


def check_config_param(param, param_name):
    if param == "" or param is None:
        raise ValueError("credentials config missing required parameters[%s]" % param_name)


def load_credentials_properties(file_name):
    if file_name is None or file_name == "":
        file_name = const.DEFAULT_CONFIG_NAME

    credential_properties = CredentialsProperties()
    config_dict = config_utils.Properties(file_name).get_properties()
    credential_properties.source_properties = config_dict
    if config_dict is not None and len(config_dict) > 0:
        init_default_config(config_dict, credential_properties)
        init_secrets_regions(config_dict, credential_properties)
        init_credentials_provider(config_dict, credential_properties)
        init_secret_names(config_dict, credential_properties)
        return credential_properties
    return None


def init_default_config(config_dict, credential_properties):
    credential_properties.private_key_path = config_dict.get(env_const.EnvClientKeyPrivateKeyPathNameKey)
    try:
        password = client_key_utils.get_password(config_dict,
                                                 env_const.ENV_CLIENT_KEY_PASSWORD_FROM_ENV_VARIABLE_NAME,
                                                 const.PROPERTIES_CLIENT_KEY_PASSWORD_FROM_FILE_PATH_NAME)
        credential_properties.password = password
    except(OSError, ValueError, Exception):
        pass


def init_secret_names(config_dict, credential_properties):
    secret_name_list = []
    secret_names = config_dict.get(const.PROPERTIES_SECRET_NAMES_KEY)
    if secret_names:
        secret_name_list.extend(secret_names.split(","))
    credential_properties.secret_name_list = secret_name_list


def init_secrets_regions(config_dict, credential_properties):
    region_info_list = []
    init_dkms_instances(config_dict, region_info_list, credential_properties)
    init_kms_regions(config_dict, region_info_list)
    credential_properties.region_info_list = region_info_list


def init_kms_regions(config_dict, region_info_list):
    region_ids = config_dict.get(env_const.ENV_CACHE_CLIENT_REGION_ID_KEY)
    if region_ids:
        try:
            region_dict_list = json.loads(region_ids)
            for region_dict in region_dict_list:
                region_info_list.append(RegionInfo(
                    None if not region_dict.get(
                        env_const.ENV_REGION_REGION_ID_NAME_KEY) else region_dict.get(
                        env_const.ENV_REGION_REGION_ID_NAME_KEY),
                    region_dict.get(env_const.ENV_REGION_VPC_NAME_KEY),
                    None if not region_dict.get(
                        env_const.ENV_REGION_ENDPOINT_NAME_KEY) else region_dict.get(
                        env_const.ENV_REGION_ENDPOINT_NAME_KEY)))
        except Exception:
            raise ValueError(("config param.get(%s) is illegal" % env_const.ENV_CACHE_CLIENT_REGION_ID_KEY))


def init_dkms_instances(config_dict, region_info_list, credential_properties):
    dkms_configs_dict = {}
    config_json = config_dict.get(env_const.CACHE_CLIENT_DKMS_CONFIG_INFO_KEY)
    if config_json:
        try:
            dkms_config_maps = json.loads(config_json)
            for dkms_config_map in dkms_config_maps:
                dkms_config = DKmsConfig()
                dkms_config.from_map(dkms_config_map)
                if not all([dkms_config.region_id, dkms_config.endpoint, dkms_config.client_key_file]):
                    raise ValueError("init properties fail, cause of cache_client_dkms_config_info param[regionId or "
                                     "endpoint or clientKeyFile] is empty")
                try:
                    password = client_key_utils.get_password(config_dict, dkms_config.password_from_env_variable,
                                                             dkms_config.password_from_file_path_name)
                    dkms_config.password = password
                except(OSError, ValueError, Exception) as e:
                    if not credential_properties.password:
                        raise e
                    dkms_config.password = credential_properties.password
                region_info = RegionInfo(region_id=dkms_config.region_id, endpoint=dkms_config.endpoint,
                                         kms_type=env_const.DKMS_TYPE)
                dkms_configs_dict[region_info] = dkms_config
                region_info_list.append(region_info)
        except Exception:
            raise ValueError(("config param.get(%s) is illegal" % env_const.CACHE_CLIENT_DKMS_CONFIG_INFO_KEY))
    credential_properties.dkms_configs_dict = dkms_configs_dict


def init_credentials_provider(config_dict, credential_properties):
    credentials_type = config_dict.get(env_const.ENV_CREDENTIALS_TYPE_KEY)
    access_key_id = config_dict.get(env_const.ENV_CREDENTIALS_ACCESS_KEY_ID_KEY)
    access_secret = config_dict.get(env_const.ENV_CREDENTIALS_ACCESS_SECRET_KEY)
    if credentials_type:
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
            password = client_key_utils.get_password(config_dict,
                                                     env_const.ENV_CLIENT_KEY_PASSWORD_FROM_ENV_VARIABLE_NAME,
                                                     const.PROPERTIES_CLIENT_KEY_PASSWORD_FROM_FILE_PATH_NAME)
            cred, signer = client_key_utils.load_rsa_key_pair_credential_and_client_key_signer(
                client_key_path, password)
            credential = ClientKeyCredential(signer, cred)
        else:
            raise ValueError(("config param.get(%s) is illegal" % env_const.ENV_CREDENTIALS_TYPE_KEY))
        credential_properties.credential = credential
