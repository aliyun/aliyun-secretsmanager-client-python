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

from openapi.models import Config


class DKmsConfig(Config):

    def __init__(self, ignore_ssl_certs=False, password_from_env_variable=None, password_from_file_path_name=None):
        super(DKmsConfig, self).__init__()
        self.ignore_ssl_certs = ignore_ssl_certs
        self.password_from_env_variable = password_from_env_variable
        self.password_from_file_path_name = password_from_file_path_name

    def from_map(self, m=None):
        super(DKmsConfig, self).from_map(m)
        if m is not None:
            if m.get('ignoreSslCerts') is not None:
                self.ignore_ssl_certs = m.get('ignoreSslCerts')
            if m.get('passwordFromEnvVariable') is not None:
                self.password_from_env_variable = m.get('passwordFromEnvVariable')
            if m.get('passwordFromFilePathName') is not None:
                self.password_from_file_path_name = m.get('passwordFromFilePathName')
