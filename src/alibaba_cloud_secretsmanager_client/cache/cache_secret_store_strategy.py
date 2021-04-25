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


class CacheSecretStoreStrategy(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def init(self):
        """初始化方法"""

    @abc.abstractmethod
    def store_secret(self, cache_secret_info):
        """缓存secret信息"""

    @abc.abstractmethod
    def get_cache_secret_info(self, secret_name):
        """获取secret缓存信息"""

    @abc.abstractmethod
    def close(self):
        """关闭资源"""
