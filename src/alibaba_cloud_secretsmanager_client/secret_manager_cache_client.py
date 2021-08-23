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


import json
import threading
import time

from aliyunsdkcore.request import RpcRequest

from alibaba_cloud_secretsmanager_client.model.secret_info import convert_json_to_secret_info
from alibaba_cloud_secretsmanager_client.utils import const, err_code_const
from alibaba_cloud_secretsmanager_client.utils.backoff_utils import judge_need_back_off, judge_need_recovery_exception
from alibaba_cloud_secretsmanager_client.utils.byte_buffer_utils import covert_string_to_byte
from alibaba_cloud_secretsmanager_client.utils.common_logger import get_logger
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkkms.request.v20160120.GetSecretValueRequest import GetSecretValueRequest
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING, STATE_STOPPED


def judge_skip_refresh_exception(e):
    return isinstance(e, ClientException) and not judge_need_back_off(e) and not (
            err_code_const.FORBIDDEN_IN_DEBT_OVER_DUE == e.error_code or err_code_const.FORBIDDEN_IN_DEBT == e.error_code)


class SecretManagerCacheClient:

    def __init__(self):
        """"""
        self.stage = const.STAGE_ACS_CURRENT
        self.secret_client = None
        self.sched = BackgroundScheduler()
        self.cache_secret_store_strategy = None
        self.cache_hook = None
        self.secret_ttl_dict = {}
        self.refresh_secret_strategy = None
        self.json_ttl_property_name = "ttl"
        self.__refresh_lock = threading.RLock()
        self.__get_cache_secret_info_lock = threading.RLock()

    def init(self):
        self.secret_client.init()
        self.cache_secret_store_strategy.init()
        self.refresh_secret_strategy.init()
        self.cache_hook.init()
        for secret_name in self.secret_ttl_dict:
            try:
                secret_info = self.__get_secret_value(secret_name)
            except ClientException as e:
                get_logger().error("action:__get_secret_value", exc_info=True)
                if judge_skip_refresh_exception(e):
                    raise e
            self.store_and_refresh(secret_name, secret_info)
        get_logger().info("SecretManagerClient init success")

    def get_secret_info(self, secret_name):
        """根据凭据名称获取secretInfo信息"""
        if secret_name is None:
            raise ValueError("the argument[secret_name] must not be null")
        cache_secret_info = self.cache_secret_store_strategy.get_cache_secret_info(secret_name)
        if cache_secret_info is not None and not self.judge_cache_expire(cache_secret_info):
            return self.cache_hook.get(cache_secret_info)
        else:
            with self.__get_cache_secret_info_lock:
                cache_secret_info = self.cache_secret_store_strategy.get_cache_secret_info(secret_name)
                if cache_secret_info is not None and not self.judge_cache_expire(cache_secret_info):
                    return self.cache_hook.get(cache_secret_info)
                secret_info = self.__get_secret_value(secret_name)
                self.store_and_refresh(secret_name, secret_info)
                return self.cache_hook.put(secret_info).secret_info if self.cache_hook.put(
                    secret_info) is not None else None

    def get_secret_value(self, secret_name):
        """根据凭据名称获取凭据存储值文本信息"""
        secret_info = self.get_secret_info(secret_name)
        if secret_info is None:
            return None
        if const.TEXT_DATA_TYPE != secret_info.secret_data_type:
            raise ValueError(("the secret named[%s] do not support text value" % secret_name))
        return secret_info.secret_value

    def get_binary_value(self, secret_name):
        """根据凭据名称获取凭据存储的二进制信息"""
        secret_info = self.get_secret_info(secret_name)
        if secret_info is None:
            return None
        if const.BINARY_DATA_TYPE != secret_info.secret_data_type:
            raise ValueError(("the secret named[%s] do not support binary value" % secret_name))
        return covert_string_to_byte(secret_info.secret_value)

    def refresh_now(self, secret_name):
        """强制刷新指定的凭据名称"""
        if secret_name is None:
            raise ValueError("the argument[secret_name] must not be null")
        return self.__refresh_now(secret_name)

    def __get_secret_value(self, secret_name):
        get_secret_request = RpcRequest('Kms', '2016-01-20', 'GetSecretValue', 'kms')
        get_secret_request._protocol_type = "https"
        get_secret_request.add_query_param('SecretName', secret_name)
        get_secret_request.add_query_param('VersionStage', self.stage)
        get_secret_request.add_query_param('FetchExtendedConfig', True)
        get_secret_request.set_accept_format("JSON")
        try:
            get_secret_resp = self.secret_client.get_secret_value(get_secret_request)
            resp_json = json.loads(get_secret_resp.decode(encoding="utf-8"))
        except ClientException as e:
            get_logger().error("action:get_secret_value", exc_info=True)
            if judge_need_recovery_exception(e):
                try:
                    secret_info = self.cache_hook.recovery_get_secret(secret_name)
                    if secret_info is not None:
                        return secret_info
                    else:
                        raise e
                except ClientException:
                    get_logger().error("action:recovery_get_secret", exc_info=True)
                    raise e
            else:
                raise e
        return convert_json_to_secret_info(resp_json)

    def judge_cache_expire(self, cache_secret_info):
        secret_info = cache_secret_info.secret_info
        ttl = self.refresh_secret_strategy.parse_ttl(secret_info)
        if ttl <= 0:
            ttl = self.secret_ttl_dict.get(secret_info.secret_name, const.DEFAULT_TTL)
        return int(round(time.time() * 1000)) - cache_secret_info.refresh_time_stamp > ttl

    def store_and_refresh(self, secret_name, secret_info):
        self.__refresh_now(secret_name, secret_info)

    def __refresh_now(self, secret_name, secret_info=None):
        with self.__refresh_lock:
            try:
                self.__refresh(secret_name, secret_info)
                self.__remove_refresh_task(secret_name)
                self.__add_refresh_task(secret_name)
                return True
            except Exception:
                get_logger().error("action:__refresh_now ", exc_info=True)
                return False

    def __refresh(self, secret_name, secret_info=None):
        if secret_info is None:
            secret_info = self.__get_secret_value(secret_name)
        cache_secret_info = self.cache_hook.put(secret_info)
        if cache_secret_info is not None:
            self.cache_secret_store_strategy.store_secret(cache_secret_info)
        get_logger().info("secret_name:%s refresh success", secret_name)

    def __remove_refresh_task(self, secret_name):
        if self.sched.get_job(job_id=secret_name) is not None:
            self.sched.remove_job(job_id=secret_name)

    def __add_refresh_task(self, secret_name):
        cache_secret_info = self.cache_secret_store_strategy.get_cache_secret_info(secret_name)
        execute_time = self.refresh_secret_strategy.parse_next_execute_time(cache_secret_info)
        if execute_time <= 0:
            refresh_time_stamp = cache_secret_info.refresh_time_stamp
            secret_ttl = self.secret_ttl_dict.get(secret_name)
            execute_time = self.refresh_secret_strategy.get_next_execute_time(secret_name,
                                                                              const.DEFAULT_TTL if secret_ttl is None else secret_ttl,
                                                                              refresh_time_stamp)
            execute_time = max(execute_time, int(round(time.time() * 1000)))
        self.sched.add_job(self.__refresh_task, 'date',
                           run_date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(execute_time / 1000)),
                           id=secret_name, args=[secret_name])
        if self.sched.state != STATE_RUNNING:
            self.sched.start()
        get_logger().info("secret_name:%s add refresh task success", secret_name)

    def __refresh_task(self, secret_name):
        try:
            self.__refresh(secret_name)
        except ClientException:
            get_logger().error("action:__refresh", exc_info=True)
        try:
            self.__add_refresh_task(secret_name)
        except ClientException:
            get_logger().error("action:__add_refresh_task", exc_info=True)
            pass

    def close(self):
        if self.cache_secret_store_strategy is not None:
            self.cache_secret_store_strategy.close()
        if self.refresh_secret_strategy is not None:
            self.refresh_secret_strategy.close()
        if self.cache_hook is not None:
            self.cache_hook.close()
        if self.secret_client is not None:
            self.secret_client.close()
        if self.sched is not None and self.sched.state is not STATE_STOPPED:
            self.sched.shutdown()
