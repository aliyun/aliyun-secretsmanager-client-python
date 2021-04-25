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


import logging

from alibaba_cloud_secretsmanager_client.cache.default_secret_cache_hook import DefaultSecretCacheHook
from alibaba_cloud_secretsmanager_client.cache.memory_cache_secret_store_strategy import MemoryCacheSecretStoreStrategy
from alibaba_cloud_secretsmanager_client.cache_client_builder import CacheClientBuilder
from alibaba_cloud_secretsmanager_client.secret_manager_cache_client import SecretManagerCacheClient
from alibaba_cloud_secretsmanager_client.service.default_refresh_secret_strategy import DefaultRefreshSecretStrategy
from alibaba_cloud_secretsmanager_client.service.default_secret_manager_client_builder import \
    BaseSecretManagerClientBuilder
from alibaba_cloud_secretsmanager_client.utils import const
from alibaba_cloud_secretsmanager_client.utils.common_logger import get_logger, set_logger


class SecretManagerCacheClientBuilder(CacheClientBuilder):

    def __init__(self):
        self.__secret_cache_client = None

    @classmethod
    def new_client(cls):
        """构建一个Secret Cache Client"""
        return SecretManagerCacheClientBuilder().build()

    @classmethod
    def new_cache_client_builder(cls, client):
        """根据指定的Secret Manager Client构建一个Cache Client Builder"""
        builder = SecretManagerCacheClientBuilder()
        builder.__build_secret_cache_client()
        builder.__secret_cache_client.secret_client = client
        return builder

    def with_secret_ttl(self, secret_name, ttl):
        """设定指定凭据名称的凭据TTL"""
        self.__build_secret_cache_client()
        self.__secret_cache_client.secret_ttl_dict[secret_name] = ttl
        return self

    def with_parse_json_ttl(self, json_ttl_property_name):
        """设定secret value解析TTL字段名称"""
        self.__build_secret_cache_client()
        self.__secret_cache_client.json_ttl_property_name = json_ttl_property_name
        return self

    def with_refresh_secret_strategy(self, refresh_secret_strategy):
        """设定secret刷新策略"""
        self.__build_secret_cache_client()
        self.__secret_cache_client.refresh_secret_strategy = refresh_secret_strategy
        return self

    def with_cache_secret_strategy(self, cache_secret_store_strategy):
        """设定secret缓存策略"""
        self.__build_secret_cache_client()
        self.__secret_cache_client.cache_secret_store_strategy = cache_secret_store_strategy
        return self

    def with_cache_stage(self, stage):
        """指定凭据Version Stage"""
        self.__build_secret_cache_client()
        self.__secret_cache_client.stage = stage
        return self

    def with_secret_cache_hook(self, cache_hook):
        """指定凭据Cache Hook"""
        self.__build_secret_cache_client()
        self.__secret_cache_client.cache_hook = cache_hook
        return self

    def with_logger(self, logger):
        """指定输出日志"""
        set_logger(logger)
        return self

    def build(self):
        """"""
        if get_logger() is None:
            logger = logging.getLogger(const.DEFAULT_LOGGER_NAME)
            set_logger(logger)
            logger.setLevel(level=logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            logger.addHandler(console)
        self.__build_secret_cache_client()
        if self.__secret_cache_client.secret_client is None:
            self.__secret_cache_client.secret_client = BaseSecretManagerClientBuilder.standard().build()
        if self.__secret_cache_client.cache_secret_store_strategy is None:
            self.__secret_cache_client.cache_secret_store_strategy = MemoryCacheSecretStoreStrategy()
        if self.__secret_cache_client.refresh_secret_strategy is None:
            self.__secret_cache_client.refresh_secret_strategy = DefaultRefreshSecretStrategy(
                self.__secret_cache_client.json_ttl_property_name)
        if self.__secret_cache_client.cache_hook is None:
            self.__secret_cache_client.cache_hook = DefaultSecretCacheHook(self.__secret_cache_client.stage)
        self.__secret_cache_client.init()
        return self.__secret_cache_client

    def __build_secret_cache_client(self):
        """"""
        if self.__secret_cache_client is None:
            self.__secret_cache_client = SecretManagerCacheClient()
