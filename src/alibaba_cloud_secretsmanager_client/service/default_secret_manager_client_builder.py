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


class BaseSecretManagerClientBuilder(CacheClientBuilder, object):
    __metaclass__ = abc.ABCMeta

    @classmethod
    def standard(cls):
        """构建T对象，同时对T对象实例进行初始化"""
        return DefaultSecretManagerClientBuilder()


class RegionInfoExtend:

    def __init__(self, region_id, endpoint=None, vpc=False, reachable=None, escaped=None):
        self.escaped = escaped
        self.reachable = reachable
        self.region_id = region_id
        self.vpc = vpc
        self.endpoint = endpoint


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
            futures.append(thread_pool_executor.submit(ping_task, RegionInfoExtend(region_info.region_id,
                                                                                   region_info.endpoint,
                                                                                   region_info.vpc)))
        if wait(futures, return_when=ALL_COMPLETED):
            for future in futures:
                region_info_extend_list.append(future.result())
        region_info_extend_list.sort(
            key=lambda rie: (not rie.reachable, rie.escaped))
        region_info_list = []
        for region_info_extend in region_info_extend_list:
            region_info_list.append(
                RegionInfo(region_info_extend.region_id,
                           region_info_extend.vpc, region_info_extend.endpoint))
        return region_info_list


def ping_task(region_info_extend):
    endpoint = region_info_extend.endpoint
    region_id = region_info_extend.region_id
    vpc = region_info_extend.vpc
    if endpoint is not None and endpoint.strip() != '':
        ping_delay = ping_host(endpoint)
    elif vpc:
        ping_delay = ping_host(get_vpc_endpoint(region_id))
    else:
        ping_delay = ping_host(get_endpoint(region_id))
    return RegionInfoExtend(region_id, endpoint, vpc, ping_delay >= 0,
                            ping_delay if ping_delay >= 0 else sys.float_info.max)


class DefaultSecretManagerClientBuilder(BaseSecretManagerClientBuilder):

    def __init__(self):
        self.region_info_list = []
        self.credential = None
        self.back_off_strategy = None

    def build(self):
        """构建T对象，同时对T对象实例进行初始化"""
        return self.DefaultSecretManagerClient(self.region_info_list, self.credential, self.back_off_strategy, self)

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

    class DefaultSecretManagerClient(SecretManagerClient):

        def __init__(self, region_info_list, credential, back_off_strategy, builder):
            self.client_dict = {}
            self.credential = credential
            self.back_off_strategy = back_off_strategy
            self.builder = builder
            self.pool = ThreadPoolExecutor(5)
            self.region_info_list = region_info_list
            self.request_waiting_time = 10 * 60
            self.signer = None

        def init(self):
            self.__init_properties()
            self.__init_env()
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
                get_secret_request = RpcRequest(get_secret_value_req._product, get_secret_value_req._version,
                                                get_secret_value_req._action_name,
                                                get_secret_value_req._location_service_code,
                                                signer=get_secret_value_req._signer)
                get_secret_request._protocol_type = get_secret_value_req._protocol_type
                get_secret_request.add_query_param('SecretName',
                                                   get_secret_value_req.get_query_params().get('SecretName'))
                get_secret_request.add_query_param('VersionStage',
                                                   get_secret_value_req.get_query_params().get('VersionStage'))
                get_secret_request.add_query_param('FetchExtendedConfig',
                                                   get_secret_value_req.get_query_params().get('FetchExtendedConfig'))
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
            region_id = region_info.region_id
            if self.client_dict.get(region_id) is not None and self.client_dict.get(region_id) != '':
                return self.client_dict.get(region_id)
            endpoint = region_info.endpoint
            vpc = region_info.vpc
            if endpoint is not None and endpoint.strip() != '':
                region_provider.add_endpoint(const.PRODUCT_NAME, region_id, endpoint)
            elif vpc is not None and vpc:
                region_provider.add_endpoint(const.PRODUCT_NAME, region_id,
                                             get_vpc_endpoint(region_id))
            client = AcsClient(credential=self.credential, region_id=region_id, verify=False)
            client.set_user_agent(get_user_agent())
            self.client_dict[region_id] = client
            return self.client_dict.get(region_id)

        def __init_properties(self):
            if self.credential is None:
                credential_properties = credentials_properties_utils.load_credentials_properties("")
                if credential_properties is not None:
                    self.credential = credential_properties.credential
                    self.region_info_list = credential_properties.region_info_list

        def __init_env(self):
            env_dict = os.environ
            if self.credential is None:
                credentials_type = env_dict.get(env_const.ENV_CREDENTIALS_TYPE_KEY)
                check_evn_param(credentials_type, env_const.ENV_CREDENTIALS_TYPE_KEY)
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
                    password = client_key_utils.get_password(env_dict)
                    credential, signer = client_key_utils.load_rsa_key_pair_credential_and_client_key_signer(
                        client_key_path, password)
                    self.credential = ClientKeyCredential(signer, credential)
                else:
                    raise ValueError(("env param.get(%s) is illegal" % env_const.ENV_CREDENTIALS_TYPE_KEY))
                if self.credential is not None:
                    if len(self.region_info_list) == 0:
                        region_json = env_dict.get(env_const.ENV_CACHE_CLIENT_REGION_ID_KEY)
                        check_evn_param(region_json, env_const.ENV_CACHE_CLIENT_REGION_ID_KEY)
                        try:
                            region_dict_list = json.loads(region_json)
                            for region_dict in region_dict_list:
                                self.region_info_list.append(RegionInfo(
                                    None if region_dict.get(
                                        env_const.ENV_REGION_REGION_ID_NAME_KEY) == '' else region_dict.get(
                                        env_const.ENV_REGION_REGION_ID_NAME_KEY),
                                    region_dict.get(env_const.ENV_REGION_VPC_NAME_KEY),
                                    None if region_dict.get(
                                        env_const.ENV_REGION_ENDPOINT_NAME_KEY) == '' else region_dict.get(
                                        env_const.ENV_REGION_ENDPOINT_NAME_KEY)))
                        except Exception:
                            raise ValueError(
                                ("env param.get(%s) is illegal" % env_const.ENV_CACHE_CLIENT_REGION_ID_KEY))

        def __del__(self):
            self.close()

        def close(self):
            if self.pool is not None:
                self.pool.shutdown()
