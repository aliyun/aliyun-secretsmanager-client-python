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


from alibaba_cloud_secretsmanager_client.cache.cache_secret_store_strategy import CacheSecretStoreStrategy


class MemoryCacheSecretStoreStrategy(CacheSecretStoreStrategy):

    def __init__(self):
        """"""
        self.__cache_map = {}

    def init(self):
        pass

    def store_secret(self, cache_secret_info):
        """缓存secret信息"""
        self.__cache_map[cache_secret_info.secret_info.secret_name] = cache_secret_info

    def get_cache_secret_info(self, secret_name):
        """获取secret缓存信息"""
        return self.__cache_map.get(secret_name)

    def close(self):
        pass
