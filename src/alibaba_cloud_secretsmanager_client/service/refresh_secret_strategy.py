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


class RefreshSecretStrategy(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def init(self):
        """初始化方法"""

    @abc.abstractmethod
    def get_next_execute_time(self, secret_name, ttl, offset):
        """获取下一次secret刷新执行的时间"""

    @abc.abstractmethod
    def parse_next_execute_time(self, cache_secret_info):
        """通过secret信息解析下一次secret刷新执行的时间"""

    @abc.abstractmethod
    def parse_ttl(self, secret_info):
        """根据凭据信息解析轮转时间间隔"""

    @abc.abstractmethod
    def close(self):
        """关闭资源"""
