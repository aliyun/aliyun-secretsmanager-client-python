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
from alibaba_cloud_secretsmanager_client.utils import err_code_const
from aliyunsdkcore.acs_exception import error_code
from aliyunsdkcore.acs_exception.exceptions import ClientException


def judge_need_back_off(e):
    if isinstance(e, ClientException):
        if (err_code_const.REJECTED_THROTTLING == e.error_code) or (
                err_code_const.SERVICE_UNAVAILABLE_TEMPORARY == e.error_code) or (
                err_code_const.INTERNAL_FAILURE == e.error_code):
            return True
    return False


def judge_need_recovery_exception(e):
    if isinstance(e, ClientException):
        if (error_code.SDK_HTTP_ERROR == e.error_code) or (err_code_const.SDK_READ_TIMEOUT == e.error_code) or (
                err_code_const.SDK_SERVER_UNREACHABLE == e.error_code) or judge_need_back_off(e):
            return True
    return False
