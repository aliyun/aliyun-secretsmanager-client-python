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
import time

from alibaba_cloud_secretsmanager_client.service.refresh_secret_strategy import RefreshSecretStrategy


class DefaultRefreshSecretStrategy(RefreshSecretStrategy):

    def __init__(self, json_ttl_property_name):
        self.__json_ttl_property_name = json_ttl_property_name

    def init(self):
        pass

    def get_next_execute_time(self, secret_name, ttl, offset):
        """获取下一次secret刷新执行的时间"""
        now = int(round(time.time() * 1000))
        if ttl + offset > now:
            return ttl + offset
        else:
            return now + ttl

    def parse_next_execute_time(self, cache_secret_info):
        """通过secret信息解析下一次secret刷新执行的时间"""
        secret_info = cache_secret_info.secret_info
        ttl = self.parse_ttl(secret_info)
        if ttl <= 0:
            return ttl
        return self.get_next_execute_time(secret_info.secret_name, ttl,
                                          cache_secret_info.refresh_time_stamp)

    def parse_ttl(self, secret_info):
        """根据凭据信息解析轮转时间间隔"""
        if self.__json_ttl_property_name is None:
            return -1
        try:
            secret_value_dict = json.loads(secret_info.secret_value)
        except Exception:
            return -1
        if secret_value_dict.get(self.__json_ttl_property_name) is None:
            return -1
        return secret_value_dict.get(self.__json_ttl_property_name)

    def close(self):
        pass
