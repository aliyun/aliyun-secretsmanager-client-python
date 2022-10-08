# coding=utf-8
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License


import abc
import json
import os
import sys
import time

from aliyunsdkcore.auth.algorithm import sha_hmac256
from aliyunsdkcore.request import RpcRequest

from alibaba_cloud_secretsmanager_client.auth.client_key_signer import ClientKeySigner
from alibaba_cloud_secretsmanager_client.cache_client_builder import CacheClientBuilder
from alibaba_cloud_secretsmanager_client.model.client_key_credentials import ClientKeyCredential
from alibaba_cloud_secretsmanager_client.model.dkms_config import DKmsConfig
from alibaba_cloud_secretsmanager_client.model.region_info import RegionInfo
from alibaba_cloud_secretsmanager_client.service.full_jitter_back_off_strategy import FullJitterBackoffStrategy
from alibaba_cloud_secretsmanager_client.service.secret_manager_client import SecretManagerClient
from alibaba_cloud_secretsmanager_client.service.user_agent_manager import register_user_agent, \
    get_user_agent
from alibaba_cloud_secretsmanager_client.utils import const, env_const, client_key_utils, config_utils, \
    credentials_properties_utils
from alibaba_cloud_secretsmanager_client.utils.backoff_utils import judge_need_recovery_exception
from alibaba_cloud_secretsmanager_client.utils.common_logger import get_logger
from alibaba_cloud_secretsmanager_client.utils.kms_end_point_utils import get_vpc_endpoint, get_endpoint
from alibaba_cloud_secretsmanager_client.utils.ping_utils import ping_host
from aliyunsdkcore.acs_exception import error_code
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.auth import credentials
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.profile import region_provider
from aliyunsdkkms.request.v20160120.GetSecretValueRequest import GetSecretValueRequest
from concurrent.futures import wait, ALL_COMPLETED, FIRST_COMPLETED
from concurrent.futures.thread import ThreadPoolExecutor

from alibabacloud_dkms_transfer.kms_transfer_acs_client import KmsTransferAcsClient


class BaseSecretManagerClientBuilder(CacheClientBuilder, object):
    __metaclass__ = abc.ABCMeta

    @classmethod
    def standard(cls):
        """构建T对象，同时对T对象实例进行初始化"""
        return DefaultSecretManagerClientBuilder()


class RegionInfoExtend:

    def __init__(self, region_id, endpoint=None, vpc=False, reachable=None, escaped=None, kms_type=env_const.KMS_TYPE):
        self.escaped = escaped
        self.reachable = reachable
        self.region_id = region_id
        self.vpc = vpc
        self.endpoint = endpoint
        self.kms_type = kms_type


def check_evn_param(param, param_name):
    if param is None:
        raise ValueError(("env param.get(%s) is required" % param_name))


def sort_region_info_list(region_info_list):
    if len(region_info_list) == 0:
        return region_info_list
    with ThreadPoolExecutor(len(region_info_list)) as thread_pool_executor:
        region_info_extend_list = []
        futures = []
        for region_info in region_info_list:
            futures.append(thread_pool_executor.submit(ping_task, RegionInfoExtend(region_id=region_info.region_id,
                                                                                   endpoint=region_info.endpoint,
                                                                                   vpc=region_info.vpc,
                                                                                   kms_type=region_info.kms_type)))
        if wait(futures, return_when=ALL_COMPLETED):
            for future in futures:
                region_info_extend_list.append(future.result())
        region_info_extend_list.sort(
            key=lambda rie: (not rie.reachable, rie.escaped))
        region_info_list = []
        for region_info_extend in region_info_extend_list:
            region_info_list.append(
                RegionInfo(region_info_extend.region_id, region_info_extend.vpc, region_info_extend.endpoint,
                           region_info_extend.kms_type))
        return region_info_list


def ping_task(region_info_extend):
    endpoint = region_info_extend.endpoint
    region_id = region_info_extend.region_id
    vpc = region_info_extend.vpc
    kms_type = region_info_extend.kms_type
    if endpoint is not None and endpoint.strip() != '':
        ping_delay = ping_host(endpoint)
    elif vpc:
        ping_delay = ping_host(get_vpc_endpoint(region_id))
    else:
        ping_delay = ping_host(get_endpoint(region_id))
    return RegionInfoExtend(region_id, endpoint, vpc, ping_delay >= 0,
                            ping_delay if ping_delay >= 0 else sys.float_info.max, kms_type)


class DefaultSecretManagerClientBuilder(BaseSecretManagerClientBuilder):

    def __init__(self):
        self.region_info_list = []
        self.credential = None
        self.back_off_strategy = None
        self.dkms_configs_dict = {}
        self.custom_config_file = None

    def build(self):
        """构建T对象，同时对T对象实例进行初始化"""
        return self.DefaultSecretManagerClient(self.region_info_list, self.credential, self.back_off_strategy,
                                               self.dkms_configs_dict, self.custom_config_file, self)

    def with_token(self, token_id, token):
        """指定token信息"""
        self.credential = credentials.AccessKeyCredential(token_id, token)
        return self

    def with_access_key(self, access_key_id, access_key_secret):
        """指定ak sk信息"""
        self.credential = credentials.AccessKeyCredential(access_key_id, access_key_secret)
        return self

    def with_credentials(self, credential):
        """指定credentials"""
        self.credential = credential
        return self

    def add_region(self, region_id):
        """指定调用地域Id"""
        self.region_info_list.append(RegionInfo(region_id))
        return self

    def add_region_info(self, region_info):
        """指定调用地域信息"""
        self.region_info_list.append(region_info)
        return self

    def with_region(self, *region_ids):
        """指定调用地域Id列表"""
        for region_id in region_ids:
            self.region_info_list.append(RegionInfo(region_id))
        return self

    def with_back_off_strategy(self, back_off_strategy):
        """指定back off 策略"""
        self.back_off_strategy = back_off_strategy
        return self

    def add_dkms_config(self, dkms_config):
        """指定专属kms配置"""
        region_info = RegionInfo(region_id=dkms_config.region_id, endpoint=dkms_config.endpoint,
                                 kms_type=env_const.DKMS_TYPE)
        self.dkms_configs_dict[region_info] = dkms_config
        self.add_region_info(region_info)
        return self

    def with_custom_config_file(self, custom_config_file):
        """指定自定义配置文件路径"""
        self.custom_config_file = custom_config_file
        return self

    class DefaultSecretManagerClient(SecretManagerClient):

        def __init__(self, region_info_list, credential, back_off_strategy, dkms_configs_dict, custom_config_file,
                     builder):
            self.client_dict = {}
            self.credential = credential
            self.back_off_strategy = back_off_strategy
            self.builder = builder
            self.pool = ThreadPoolExecutor(5)
            self.region_info_list = region_info_list
            self.request_waiting_time = 10 * 60
            self.signer = None
            self.dkms_configs_dict = dkms_configs_dict
            self.custom_config_file = custom_config_file

        def init(self):
            self.__init_from_config_file()
            self.__init_from_env()
            if not self.region_info_list:
                raise ValueError("the param[regionInfo] is needed")
            if not self.dkms_configs_dict and not self.credential:
                raise ValueError("the param[credentials] is needed")
            if isinstance(self.credential, ClientKeyCredential):
                self.signer = self.credential.singer
                self.credential = self.credential.credential
            register_user_agent(
                const.USER_AGENT_OF_SECRETS_MANAGER_PYTHON + "/" + const.PROJECT_VERSION, 0)
            if self.back_off_strategy is None:
                self.back_off_strategy = FullJitterBackoffStrategy()
            self.back_off_strategy.init()
            self.region_info_list = sort_region_info_list(self.region_info_list)

        def get_secret_value(self, get_secret_value_req):
            futures = []
            finished = []
            if self.signer is not None and isinstance(self.signer, ClientKeySigner):
                get_secret_value_req._signer = sha_hmac256
            for i in range(len(self.region_info_list)):
                if i == 0:
                    try:
                        return self.__get_secret_value(self.region_info_list[i], get_secret_value_req)
                    except ClientException as e:
                        get_logger().error("action:__get_secret_value", exc_info=True)
                        if not judge_need_recovery_exception(e):
                            raise e
                get_secret_request = GetSecretValueRequest()
                get_secret_request.set_SecretName(get_secret_value_req.get_SecretName())
                get_secret_request.set_VersionStage(get_secret_value_req.get_VersionStage())
                get_secret_request.set_FetchExtendedConfig(get_secret_value_req.get_FetchExtendedConfig())
                get_secret_request.set_accept_format(get_secret_value_req.get_accept_format())
                get_secret_request._signer = get_secret_value_req._signer
                future = self.pool.submit(self.__retry_get_secret_value,
                                          get_secret_request, self.region_info_list[i], finished)
                futures.append(future)
            try:
                if wait(futures, self.request_waiting_time, return_when=FIRST_COMPLETED):
                    for future in futures:
                        if not future.done():
                            future.cancel()
                        else:
                            return future.result()
            except Exception as e:
                get_logger().error("action:__retry_get_secret_value_task", exc_info=True)
                raise e
            finally:
                finished.append(True)
            raise ClientException(error_code.SDK_HTTP_ERROR, "refreshSecretTask fail")

        def __retry_get_secret_value(self, get_secret_value_req, region_info, finished):
            retry_times = 0
            while True:
                if len(finished) > 0 and finished[0]:
                    return None
                wait_time_exponential = self.back_off_strategy.get_wait_time_exponential(retry_times)
                if wait_time_exponential < 0:
                    raise ClientException(error_code.SDK_HTTP_ERROR, "Times limit exceeded")
                time.sleep(wait_time_exponential / 1000)
                try:
                    return self.__get_secret_value(region_info, get_secret_value_req)
                except ClientException as e:
                    get_logger().error("action:__get_secret_value", exc_info=True)
                    if not judge_need_recovery_exception(e):
                        raise e
                retry_times += 1

        def __get_secret_value(self, region_info, get_secret_value_req):
            status, headers, body, exception = self.__get_client(region_info)._implementation_of_do_action(
                get_secret_value_req, self.signer)
            if exception is not None:
                raise exception
            return body

        def __get_client(self, region_info):
            if self.client_dict.get(region_info) is not None:
                return self.client_dict.get(region_info)
            if region_info.kms_type == env_const.DKMS_TYPE:
                self.client_dict[region_info] = self.__build_dkms_transfer_client(region_info)
            else:
                self.client_dict[region_info] = self.__build_kms_client(region_info)
            return self.client_dict.get(region_info)

        def __build_kms_client(self, region_info):
            region_id = region_info.region_id
            endpoint = region_info.endpoint
            vpc = region_info.vpc
            if endpoint is not None and endpoint.strip() != '':
                region_provider.add_endpoint(const.PRODUCT_NAME, region_id, endpoint)
            elif vpc is not None and vpc:
                region_provider.add_endpoint(const.PRODUCT_NAME, region_id, get_vpc_endpoint(region_id))
            client = AcsClient(credential=self.credential, region_id=region_id, verify=False)
            client.set_user_agent(get_user_agent())
            return client

        def __build_dkms_transfer_client(self, region_info):
            dkms_config = self.dkms_configs_dict[region_info]
            if dkms_config is None:
                raise ValueError('unrecognized regionInfo')
            config = dkms_config
            config.region_id = region_info.region_id
            config.endpoint = region_info.endpoint
            credential = credentials.AccessKeyCredential(env_const.PRETEND_AK, env_const.PRETEND_SK)
            if isinstance(dkms_config.ignore_ssl_certs, bool):
                dkms_config.ignore_ssl_certs = not dkms_config.ignore_ssl_certs
            client = KmsTransferAcsClient(config=config, credential=credential, verify=dkms_config.ignore_ssl_certs)
            client.set_user_agent(get_user_agent())
            return client

        def __init_from_config_file(self):
            credential_properties = credentials_properties_utils.load_credentials_properties(self.custom_config_file)
            if credential_properties is not None:
                self.credential = credential_properties.credential
                self.region_info_list.extend(credential_properties.region_info_list)
                self.dkms_configs_dict.update(credential_properties.dkms_configs_dict)

        def __init_from_env(self):
            env_dict = os.environ
            self.__init_credentials_provider_from_env(env_dict)
            self.__init_dkms_instances_from_env(env_dict)
            self.__init_kms_regions_from_env(env_dict)

        def __init_credentials_provider_from_env(self, env_dict):
            credentials_type = env_dict.get(env_const.ENV_CREDENTIALS_TYPE_KEY)
            if credentials_type:
                access_key_id = env_dict.get(env_const.ENV_CREDENTIALS_ACCESS_KEY_ID_KEY)
                access_secret = env_dict.get(env_const.ENV_CREDENTIALS_ACCESS_SECRET_KEY)
                if credentials_type == "ak":
                    check_evn_param(access_key_id, env_const.ENV_CREDENTIALS_ACCESS_KEY_ID_KEY)
                    check_evn_param(access_secret, env_const.ENV_CREDENTIALS_ACCESS_SECRET_KEY)
                    self.credential = credentials.AccessKeyCredential(access_key_id, access_secret)
                elif credentials_type == "token":
                    access_token_id = env_dict.get(env_const.ENV_CREDENTIALS_ACCESS_TOKEN_ID_KEY)
                    access_token = env_dict.get(env_const.ENV_CREDENTIALS_ACCESS_TOKEN_KEY)
                    check_evn_param(access_token_id, env_const.ENV_CREDENTIALS_ACCESS_TOKEN_KEY)
                    check_evn_param(access_token, env_const.ENV_CREDENTIALS_ACCESS_TOKEN_ID_KEY)
                    self.credential = credentials.AccessKeyCredential(access_token_id, access_token)
                elif credentials_type == "ram_role" or credentials_type == "sts":
                    role_session_name = env_dict.get(env_const.ENV_CREDENTIALS_ROLE_SESSION_NAME_KEY)
                    role_arn = env_dict.get(env_const.ENV_CREDENTIALS_ROLE_ARN_KEY)
                    check_evn_param(access_key_id, env_const.ENV_CREDENTIALS_ACCESS_KEY_ID_KEY)
                    check_evn_param(access_secret, env_const.ENV_CREDENTIALS_ACCESS_SECRET_KEY)
                    check_evn_param(role_session_name, env_const.ENV_CREDENTIALS_ROLE_SESSION_NAME_KEY)
                    check_evn_param(role_arn, env_const.ENV_CREDENTIALS_ROLE_ARN_KEY)
                    self.credential = credentials.RamRoleArnCredential(access_key_id, access_secret,
                                                                       role_arn, role_session_name)
                elif credentials_type == "ecs_ram_role":
                    role_name = env_dict.get(env_const.ENV_CREDENTIALS_ROLE_NAME_KEY)
                    check_evn_param(role_name, env_const.ENV_CREDENTIALS_ROLE_NAME_KEY)
                    self.credential = credentials.EcsRamRoleCredential(role_name)
                elif credentials_type == "client_key":
                    client_key_path = env_dict.get(env_const.EnvClientKeyPrivateKeyPathNameKey)
                    check_evn_param(client_key_path, env_const.EnvClientKeyPrivateKeyPathNameKey)
                    password = client_key_utils.get_password(env_dict,
                                                             env_const.ENV_CLIENT_KEY_PASSWORD_FROM_ENV_VARIABLE_NAME,
                                                             const.PROPERTIES_CLIENT_KEY_PASSWORD_FROM_FILE_PATH_NAME)
                    credential, signer = client_key_utils.load_rsa_key_pair_credential_and_client_key_signer(
                        client_key_path, password)
                    self.credential = ClientKeyCredential(signer, credential)
                else:
                    raise ValueError(("env param.get(%s) is illegal" % env_const.ENV_CREDENTIALS_TYPE_KEY))

        def __init_dkms_instances_from_env(self, env_dict):
            config_json = env_dict.get(env_const.CACHE_CLIENT_DKMS_CONFIG_INFO_KEY)
            if config_json:
                try:
                    dkms_config_maps = json.loads(config_json)
                    for dkms_config_map in dkms_config_maps:
                        dkms_config = DKmsConfig()
                        dkms_config.from_map(dkms_config_map)
                        if not all([dkms_config.region_id, dkms_config.endpoint, dkms_config.client_key_file]):
                            raise ValueError(
                                "init env fail, cause of cache_client_dkms_config_info param[regionId or endpoint or "
                                "clientKeyFile] is empty")
                        password = client_key_utils.get_password(env_dict, dkms_config.password_from_env_variable,
                                                                 dkms_config.password_from_file_path_name)
                        dkms_config.password = password
                        region_info = RegionInfo(region_id=dkms_config.region_id, endpoint=dkms_config.endpoint,
                                                 kms_type=env_const.DKMS_TYPE)
                        self.dkms_configs_dict[region_info] = dkms_config
                        self.region_info_list.append(region_info)
                except Exception:
                    raise ValueError(("env param.get(%s) is illegal" % env_const.CACHE_CLIENT_DKMS_CONFIG_INFO_KEY))

        def __init_kms_regions_from_env(self, env_dict):
            region_json = env_dict.get(env_const.ENV_CACHE_CLIENT_REGION_ID_KEY)
            if region_json:
                try:
                    region_dict_list = json.loads(region_json)
                    for region_dict in region_dict_list:
                        self.region_info_list.append(RegionInfo(
                            None if not region_dict.get(
                                env_const.ENV_REGION_REGION_ID_NAME_KEY) else region_dict.get(
                                env_const.ENV_REGION_REGION_ID_NAME_KEY),
                            region_dict.get(env_const.ENV_REGION_VPC_NAME_KEY),
                            None if not region_dict.get(
                                env_const.ENV_REGION_ENDPOINT_NAME_KEY) else region_dict.get(
                                env_const.ENV_REGION_ENDPOINT_NAME_KEY)))
                except Exception:
                    raise ValueError(
                        ("env param.get(%s) is illegal" % env_const.ENV_CACHE_CLIENT_REGION_ID_KEY))

        def __del__(self):
            self.close()

        def close(self):
            if self.pool is not None:
                self.pool.shutdown()
