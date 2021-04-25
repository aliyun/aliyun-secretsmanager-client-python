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


from alibaba_cloud_secretsmanager_client.service.back_off_strategy import BackoffStrategy
from alibaba_cloud_secretsmanager_client.utils import const


class FullJitterBackoffStrategy(BackoffStrategy):

    def __init__(self, retry_max_attempts=const.DEFAULT_RETRY_MAX_ATTEMPTS,
                 retry_initial_interval_mills=const.DEFAULT_RETRY_INITIAL_INTERVAL_MILLS,
                 capacity=const.DEFAULT_CAPACITY):
        self.retry_max_attempts = retry_max_attempts
        self.retry_initial_interval_mills = retry_initial_interval_mills
        self.capacity = capacity

    def init(self):
        pass

    def get_wait_time_exponential(self, retry_times):
        """获取规避等待时间"""
        if retry_times > self.retry_max_attempts:
            return -1
        return min(self.capacity, pow(2, retry_times) * self.retry_initial_interval_mills)
