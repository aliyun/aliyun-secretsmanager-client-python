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


import time

from alibaba_cloud_secretsmanager_client.cache.secret_cache_hook import SecretCacheHook
from alibaba_cloud_secretsmanager_client.model.secret_info import CacheSecretInfo


class DefaultSecretCacheHook(SecretCacheHook):

    def __init__(self, stage=None):
        """"""
        self.stage = stage

    def init(self):
        pass

    def put(self, secret_info):
        """将secret对象转化为Cache secret对象"""
        return CacheSecretInfo(secret_info=secret_info, stage=self.stage,
                               refresh_time_stamp=int(round(time.time() * 1000)))

    def get(self, cache_secret_info):
        """将Cache secret对象转化为secret对象"""
        return cache_secret_info.secret_info

    def recovery_get_secret(self, secret_name):
        """恢复凭据信息"""
        return None

    def close(self):
        pass
